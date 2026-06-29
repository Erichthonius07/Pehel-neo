with open('app/api/v1/endpoints/me.py', 'r', encoding='utf-8') as f:
    content = f.read()

old_block = '''        result.append({
            "id": issue.id,
            "category": issue.category,
            "state": issue.state,
            "title": issue.title,
            "geo_lat": float(issue.geo_lat) if issue.geo_lat else 0.0,
            "geo_lng": float(issue.geo_lng) if issue.geo_lng else 0.0,
            "severity": issue.severity,
            "ward_id": issue.ward_id,
            "support_count": issue.support_count,
            "priority_score": int(issue.priority_score) if issue.priority_score else 0,
            "ai_summary": issue.ai_summary,
            "sla_status": _compute_sla_status(issue),
            "last_commented_at": last_commented,
            "my_comment_count": comment_count,
        })'''

new_block = '''        result.append({
            "id": issue.id,
            "category": issue.category,
            "state": issue.state,
            "title": issue.title,
            "geo_lat": float(issue.geo_lat) if issue.geo_lat else 0.0,
            "geo_lng": float(issue.geo_lng) if issue.geo_lng else 0.0,
            "severity": issue.severity,
            "ward_id": issue.ward_id,
            "support_count": issue.support_count,
            "priority_score": int(issue.priority_score) if issue.priority_score else 0,
            "ai_summary": issue.ai_summary,
            "sla_ack_deadline": issue.sla_ack_deadline,
            "sla_resolution_deadline": issue.sla_resolution_deadline,
            "created_at": issue.created_at,
            "last_commented_at": last_commented,
            "my_comment_count": comment_count,
        })'''

content = content.replace(old_block, new_block)

with open('app/api/v1/endpoints/me.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("Fixed me.py - added missing created_at and SLA fields")