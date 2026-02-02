#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import hashlib
import json
import logging
import os
import re
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple


def load_neo4j_config() -> Dict[str, str]:
    base_dir = Path(__file__).resolve().parents[2]
    cfg_path = (
        base_dir
        / 'infrastructure'
        / 'config'
        / 'database'
        / 'knowledge_graph_config.json'
    )
    uri = os.getenv('KNOWLEDGE_GRAPH_NEO4J_URI', 'bolt://localhost:7687')
    user = os.getenv('KNOWLEDGE_GRAPH_NEO4J_USER', 'neo4j')
    password = os.getenv('KNOWLEDGE_GRAPH_NEO4J_PASSWORD', '')
    database = os.getenv('KNOWLEDGE_GRAPH_NEO4J_DATABASE', 'neo4j')
    if cfg_path.exists():
        try:
            with open(cfg_path, 'r', encoding='utf-8') as f:
                cfg = json.load(f)
                neo = cfg.get('knowledge_graph', {}).get('neo4j', {})
                uri = neo.get('uri', uri)
                user = neo.get('user', user)
                password = neo.get('password', password)
                database = neo.get('database', database)
8except Exception as e:
8    # 记录异常但不中断流程
8    logger.debug(f"[neo4j_law_importer] Exception: {e}")
    return {'uri': uri, 'user': user, 'password': password, 'database': database}


CHN_NUM = '一二三四五六七八九十零百千万1234567890'
ARTICLE_RE = re.compile(rf"^第([{CHN_NUM}]+)条")
DATE_RE = re.compile(r"(\d{4})-(\d{1,2})-(\d{1,2})")
DATE_CN_RE = re.compile(r"(\d{4})年(\d{1,2})月(\d{1,2})日")


def get_level_by_folder(rel_path: Path) -> str:
    top = rel_path.parts[0]
    if re.match(
        r"^((司法解释)|(地方性法规)|(宪法)|(案例)|(行政法规)|(部门规章))$", top
    ):
        return top
    return '法律'


def normalize_title_from_filename(name: str) -> Tuple[str, Optional[str]]:
    m = re.search(r"\((\d{4}-\d{2}-\d{2})\)", name)
    pub = m.group(1) if m else None
    title = re.sub(r"\(\d{4}-\d{2}-\d{2}\)', '", name).strip()
    return title, pub


def hash_id(s: str) -> str:
    return hashlib.sha1(s.encode('utf-8')).hexdigest()[:16]


def parse_markdown_file(path: Path) -> Dict[str, any]:
    lines = []
    with open(path, 'r', encoding='utf-8') as f:
        for line in f.readlines():
            lines.append(line.rstrip("\n"))
    title = None
    publish_date = None
    valid_from = None
    info_done = False
    body_start_idx = 0
    for i, line in enumerate(lines[:50]):
        if not title and line.startswith('# '):
            title = line[2:].strip()
        cn = DATE_CN_RE.search(line)
        if cn:
            dt = f"{cn.group(1)}-{int(cn.group(2)):02d}-{int(cn.group(3)):02d}"
            if '施行' in line or '生效' in line:
                valid_from = valid_from or dt
            else:
                publish_date = publish_date or dt
        if line.strip() == '<!-- INFO END -->':
            info_done = True
            body_start_idx = i + 1
            break
    if not title:
        title, publish_date_fn = normalize_title_from_filename(path.stem)
        publish_date = publish_date or publish_date_fn
    body = lines[body_start_idx:]
    articles = []
    current = None
    for line in body:
        m = ARTICLE_RE.match(line.strip())
        if m:
            if current:
                articles.append(current)
            current = {'number': m.group(1), 'text': line.strip(), 'content': []}
        else:
            if current:
                if line.strip():
                    current['content'].append(line.strip())
    if current:
        articles.append(current)
    return {
        'title': title,
        'publish_date': publish_date,
        'valid_from': valid_from,
        'articles': articles,
    }


def make_ids(
    rel_path: Path, parsed: Dict[str, any]
) -> Tuple[str, List[Tuple[str, Dict[str, any]]]]:
    law_key = (
        f"LAW::{str(rel_path)}::{parsed['title']}::{parsed.get('publish_date') or ''}"
    )
    law_id = hash_id(law_key)
    article_ids = []
    for a in parsed['articles']:
        aid = hash_id(f"ARTICLE::{law_id}::{a['number']}")
        article_ids.append((aid, a))
    return law_id, article_ids


def import_to_neo4j(base_dir: str) -> Any:
    cfg = load_neo4j_config()
    from neo4j import GraphDatabase

    driver = GraphDatabase.driver(cfg['uri'], auth=(cfg['user'], cfg['password']))
    project_root = Path(base_dir)
    with driver.session(database=cfg['database']) as session:
        try:
            session.run(
                'CREATE CONSTRAINT entity_id_unique IF NOT EXISTS FOR (n:Entity) REQUIRE n.id IS UNIQUE'
            )
8except Exception as e:
8    # 记录异常但不中断流程
8    logger.debug(f"[neo4j_law_importer] Exception: {e}")
        try:
            session.run(
                'CREATE INDEX entity_type_index IF NOT EXISTS FOR (n:Entity) ON (n.entity_type)'
            )
8except Exception as e:
8    # 记录异常但不中断流程
8    logger.debug(f"[neo4j_law_importer] Exception: {e}")
        try:
            session.run(
                'CREATE INDEX entity_title_index IF NOT EXISTS FOR (n:Entity) ON (n.title)'
            )
8except Exception as e:
8    # 记录异常但不中断流程
8    logger.debug(f"[neo4j_law_importer] Exception: {e}")
        files = []
        for p in project_root.glob('**/*.md'):
            if p.name == '_index.md':
                continue
            rel = p.relative_to(project_root)
            level = get_level_by_folder(rel)
            parsed = parse_markdown_file(p)
            if not parsed.get('title'):
                continue
            law_id, article_ids = make_ids(rel, parsed)
            props = {
                'id': law_id,
                'entity_type': 'law',
                'title': parsed['title'],
                'level': level,
                'publish_date': parsed.get('publish_date'),
                'valid_from': parsed.get('valid_from'),
                'kg_domain': 'professional',
                'source': 'Laws-1.0.0',
                'path': str(rel),
                'created_at': datetime.now().isoformat(),
            }
            session.run(
                'MERGE (n:Entity {id: $id}) SET n.entity_type=$entity_type, n.title=$title, n.level=$level, n.publish_date=$publish_date, n.valid_from=$valid_from, n.kg_domain=$kg_domain, n.source=$source, n.path=$path, n.created_at=$created_at',
                **props,
            )
            for aid, a in article_ids:
                aprops = {
                    'id': aid,
                    'entity_type': 'legal_article',
                    'title': f"第{a['number']}条",
                    'number': a['number'],
                    'text': a['text'],
                    'content': "\n".join(a['content']),
                    'kg_domain': 'professional',
                    'created_at': datetime.now().isoformat(),
                }
                session.run(
                    'MERGE (n:Entity {id: $id}) SET n.entity_type=$entity_type, n.title=$title, n.number=$number, n.text=$text, n.content=$content, n.kg_domain=$kg_domain, n.created_at=$created_at',
                    **aprops,
                )
                session.run(
                    'MATCH (a:Entity {id:$aid}), (l:Entity {id:$lid}) MERGE (a)-[r:BELONGS_TO]->(l) SET r.created_at=$ts',
                    aid=aid,
                    lid=law_id,
                    ts=datetime.now().isoformat(),
                )
    driver.close()


def summarize(cfg: Dict[str, str]) -> Dict[str, any]:
    from neo4j import GraphDatabase

    driver = GraphDatabase.driver(cfg['uri'], auth=(cfg['user'], cfg['password']))
    out = {}
    with driver.session(database=cfg['database']) as session:
        r1 = session.run("MATCH (n:Entity{entity_type:'law'}) RETURN COUNT(n) as c")
        out['laws'] = r1.single()['c'] if r1.peek() else 0
        r2 = session.run(
            "MATCH (n:Entity{entity_type:'legal_article'}) RETURN COUNT(n) as c"
        )
        out['articles'] = r2.single()['c'] if r2.peek() else 0
        r3 = session.run(
            "MATCH (:Entity{entity_type:'legal_article'})-[r:BELONGS_TO]->(:Entity{entity_type:'law'}) RETURN COUNT(r) as c"
        )
        out['belongs_relations'] = r3.single()['c'] if r3.peek() else 0
    driver.close()
    return out


def main() -> None:
    base_dir = os.environ.get(
        'LAWS_BASE_DIR',
        str(Path(__file__).resolve().parents[2] / 'projects' / 'Laws-1.0.0'),
    )
    cfg = load_neo4j_config()
    import_to_neo4j(base_dir)
    stats = summarize(cfg)
    print(json.dumps({'summary': stats}, ensure_ascii=False))


if __name__ == '__main__':
    main()
