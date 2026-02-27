import sys; sys.path.insert(0, '.')
from app.db.curation import add_to_pool, init_curation_db
from app.engine.detector import ALL_FEATURE_NAMES

def get_empty_feature_dict():
    return {f: 0 for f in ALL_FEATURE_NAMES}
    
init_curation_db()
for i in range(60):
    f = get_empty_feature_dict()
    f['url_length'] = 150
    f['url_at_symbol'] = 1
    f['nlp_urgency_score'] = 0.9
    add_to_pool(f'test_hash_auto_{i}', f, 1, 'Simulated_Analyst', 'APPROVED')
print('Added 60 mock approved samples.')
