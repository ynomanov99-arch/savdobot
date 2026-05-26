import sys
sys.path.insert(0, '.')
from utils.color_parser import normalize_color_code, is_color_query
text = '23/33'
print('is_color_query:', is_color_query(text))
print('normalize:', normalize_color_code(text))