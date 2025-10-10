import re
from typing import Literal, List


class QueryFilter:
    def __init__(self, field: str, value: str, operator: Literal['includes', 'equals', 'has_capability']):
        self.field = field
        self.value = value
        self.operator = operator


class GeneralFilter:
    def __init__(self, term: str, fields: List[str]):
        self.term = term
        self.fields = fields


class ParsedQuery:
    def __init__(self):
        self.field_filters: List[QueryFilter] = []
        self.general_filters: List[GeneralFilter] = []


class QueryParser:
    @staticmethod
    def parse(query: str) -> ParsedQuery:
        result = ParsedQuery()

        if not query or not query.strip():
            return result

        parts = re.findall(r'(?:[^\s"]+|"[^"]*")+', query)

        for part in parts:
            value = part
            if value.startswith('"') and value.endswith('"'):
                value = value[1:-1]

            if ':' in part:
                field, *value_parts = part.split(':', 1)
                field_value = ':'.join(value_parts)
                if field_value.startswith('"') and field_value.endswith('"'):
                    field_value = field_value[1:-1]

                if field and field_value:
                    if field.lower() == 'capability':
                        result.field_filters.append(QueryFilter('capabilities', field_value, 'has_capability'))
                    else:
                        result.field_filters.append(QueryFilter(field, field_value, 'includes'))
            else:
                result.general_filters.append(GeneralFilter(value, ['name', 'description', 'id']))
        
        return result