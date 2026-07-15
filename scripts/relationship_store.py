#!/usr/bin/env python3
from __future__ import annotations
import json, os, shutil, sqlite3, uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional, List
SCHEMA_VERSION=1
def default_vault_path():
    home=os.environ.get('HERMES_HOME')
    if home:
        return Path(home).expanduser().resolve()/'data'/'relationship-map'
    return Path.home()/'.hermes'/'data'/'relationship-map'
class RelationshipStore:
    def __init__(self, vault=None):
        self.vault=(Path(vault).expanduser().resolve() if vault else default_vault_path()); self.vault.mkdir(parents=True, exist_ok=True); (self.vault/'backups').mkdir(exist_ok=True)
        self.db_path=self.vault/'relationship_map.db'; self.conn=sqlite3.connect(self.db_path); self.conn.row_factory=sqlite3.Row; self.migrate()
    def close(self): self.conn.close()
    def migrate(self):
        c=self.conn.cursor(); c.execute('CREATE TABLE IF NOT EXISTS meta (key TEXT PRIMARY KEY,value TEXT NOT NULL)')
        c.execute('''CREATE TABLE IF NOT EXISTS contacts (id TEXT PRIMARY KEY,name TEXT NOT NULL,city TEXT,organization TEXT,role TEXT,tags TEXT NOT NULL DEFAULT '[]',created_at TEXT NOT NULL,updated_at TEXT NOT NULL,last_interaction_at TEXT,next_touch_at TEXT,facts TEXT NOT NULL DEFAULT '[]',inferences TEXT NOT NULL DEFAULT '[]',private_json TEXT NOT NULL DEFAULT '{}',metrics TEXT NOT NULL DEFAULT '{}',metric_evidence TEXT NOT NULL DEFAULT '{}',deleted INTEGER NOT NULL DEFAULT 0)''')
        c.execute('''CREATE TABLE IF NOT EXISTS timeline_events (id TEXT PRIMARY KEY,contact_id TEXT NOT NULL,timestamp TEXT NOT NULL,event_type TEXT NOT NULL,summary TEXT NOT NULL,metric_changes TEXT NOT NULL DEFAULT '[]',source TEXT,confidence TEXT)''')
        c.execute('''CREATE TABLE IF NOT EXISTS audit_log (id TEXT PRIMARY KEY,timestamp TEXT NOT NULL,operation TEXT NOT NULL,contact_id TEXT,preview TEXT NOT NULL,confirmed INTEGER NOT NULL DEFAULT 0)''')
        c.execute('CREATE INDEX IF NOT EXISTS idx_contacts_city_updated ON contacts(city,updated_at DESC)'); c.execute('CREATE INDEX IF NOT EXISTS idx_contacts_deleted_updated ON contacts(deleted,updated_at DESC)'); c.execute('CREATE INDEX IF NOT EXISTS idx_timeline_contact_time ON timeline_events(contact_id,timestamp DESC)')
        c.execute('INSERT OR REPLACE INTO meta(key,value) VALUES(?,?)',('schema_version',str(SCHEMA_VERSION))); self.conn.commit()
    def backup(self, reason='manual'):
        ts=datetime.utcnow().strftime('%Y%m%d_%H%M%S_%f'); dst=self.vault/'backups'/f'relationship_map_{ts}_{reason}.db'; self.conn.commit(); shutil.copy2(self.db_path,dst); return dst
    def append_timeline(self, contact_id,event_type,summary,metric_changes=None,source='',confidence=''):
        eid='evt_'+uuid.uuid4().hex; ts=datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')
        self.conn.execute('INSERT INTO timeline_events(id,contact_id,timestamp,event_type,summary,metric_changes,source,confidence) VALUES(?,?,?,?,?,?,?,?)',(eid,contact_id,ts,event_type,summary,json.dumps(metric_changes or [],ensure_ascii=False),source,confidence)); return eid
    def upsert_contact(self,data:Dict[str,Any],confirmed=False):
        if not confirmed: raise PermissionError('contact writes require explicit confirmation')
        now=datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S'); cid=data.get('id') or 'contact_'+uuid.uuid4().hex; created=data.get('created_at') or now
        self.conn.execute('''INSERT INTO contacts(id,name,city,organization,role,tags,created_at,updated_at,last_interaction_at,next_touch_at,facts,inferences,private_json,metrics,metric_evidence,deleted) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,0) ON CONFLICT(id) DO UPDATE SET name=excluded.name,city=excluded.city,organization=excluded.organization,role=excluded.role,tags=excluded.tags,updated_at=excluded.updated_at,last_interaction_at=excluded.last_interaction_at,next_touch_at=excluded.next_touch_at,facts=excluded.facts,inferences=excluded.inferences,private_json=excluded.private_json,metrics=excluded.metrics,metric_evidence=excluded.metric_evidence''',(cid,data['name'],data.get('city',''),data.get('organization',''),data.get('role',''),json.dumps(data.get('tags',[]),ensure_ascii=False),created,now,data.get('last_interaction_at',''),data.get('next_touch_at',''),json.dumps(data.get('facts',[]),ensure_ascii=False),json.dumps(data.get('inferences',[]),ensure_ascii=False),json.dumps(data.get('private',{}),ensure_ascii=False),json.dumps(data.get('metrics',{}),ensure_ascii=False),json.dumps(data.get('metric_evidence',{}),ensure_ascii=False)))
        self.append_timeline(cid,'confirmed_upsert','确认新增/更新联系人',source='user_confirmed'); self.conn.commit(); return cid
    def list_contacts(self,page=1,page_size=15,query='',city='',sort='updated_desc'):
        page=max(1,int(page)); page_size=min(50,max(1,int(page_size))); where=['deleted=0']; params=[]
        if query: where.append('(name LIKE ? OR organization LIKE ? OR tags LIKE ?)'); q=f'%{query}%'; params += [q,q,q]
        if city: where.append('city=?'); params.append(city)
        ws=' AND '.join(where); total=self.conn.execute(f'SELECT COUNT(*) FROM contacts WHERE {ws}',params).fetchone()[0]; order='updated_at DESC' if sort=='updated_desc' else 'name ASC'
        rows=self.conn.execute(f'SELECT * FROM contacts WHERE {ws} ORDER BY {order} LIMIT ? OFFSET ?',params+[page_size,(page-1)*page_size]).fetchall()
        return {'total':total,'page':page,'page_size':page_size,'query':query,'city':city,'sort':sort,'rows':[dict(r) for r in rows],'has_next':page*page_size<total}
    def get_contact(self,contact_id):
        r=self.conn.execute('SELECT * FROM contacts WHERE id=? AND deleted=0',(contact_id,)).fetchone()
        if not r: raise KeyError(contact_id)
        d=dict(r)
        for k in ['tags','facts','inferences']: d[k]=json.loads(d[k] or '[]')
        for k in ['private_json','metrics','metric_evidence']: d[k]=json.loads(d[k] or '{}')
        ev=self.conn.execute('SELECT * FROM timeline_events WHERE contact_id=? ORDER BY timestamp DESC LIMIT 50',(contact_id,)).fetchall(); d['timeline']=[dict(e) for e in ev]; return d
    def propose_operation(self,operation,contact_id='',payload=None):
        allowed={'delete','merge','bulk_import','sensitive_label','risk_assessment','trust_assessment','update'}
        if operation not in allowed: raise ValueError('unsupported operation')
        prop={'id':'prop_'+uuid.uuid4().hex,'operation':operation,'contact_id':contact_id,'payload':payload or {},'requires_confirmation':True,'preview':f'{operation}:{contact_id}'}
        self.conn.execute('INSERT INTO audit_log(id,timestamp,operation,contact_id,preview,confirmed) VALUES(?,?,?,?,?,0)',(prop['id'],datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S'),operation,contact_id,json.dumps(prop,ensure_ascii=False))); self.conn.commit(); return prop
    def apply_confirmed(self,proposal,confirmed=False):
        if not confirmed: raise PermissionError('operation requires confirmation')
        self.backup(proposal['operation']); op=proposal['operation']; cid=proposal.get('contact_id','')
        if op=='delete': self.conn.execute('UPDATE contacts SET deleted=1,updated_at=? WHERE id=?',(datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S'),cid)); self.append_timeline(cid,'confirmed_delete','确认删除/归档联系人')
        elif op in {'sensitive_label','risk_assessment','trust_assessment','update'}:
            c=self.get_contact(cid); metrics=c['metrics']; evidence=c['metric_evidence']; payload=proposal.get('payload',{})
            if 'metric' in payload:
                metrics[payload['metric']]=payload.get('value',''); evidence[payload['metric']]=payload.get('evidence','用户确认')
                self.conn.execute('UPDATE contacts SET metrics=?,metric_evidence=?,updated_at=? WHERE id=?',(json.dumps(metrics,ensure_ascii=False),json.dumps(evidence,ensure_ascii=False),datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S'),cid))
            self.append_timeline(cid,f'confirmed_{op}',f'确认执行 {op}')
        elif op in {'merge','bulk_import'} and cid: self.append_timeline(cid,f'confirmed_{op}',f'确认执行 {op}（模拟层不做破坏性自动合并）')
        self.conn.execute('UPDATE audit_log SET confirmed=1 WHERE id=?',(proposal['id'],)); self.conn.commit()
