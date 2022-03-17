from functools import partial
from datetime import datetime, timedelta
from api.schemas import ObservableSchema
from api.utils import get_json, get_jwt, jsonify_data, jsonify_errors, format_docs  # MODIFY THIS LINE
from flask import Blueprint, current_app, jsonify, g


def group_observables(relay_input):
    # Leave only unique observables ( deduplicate observable )  and select some specific observable type
    result = []
    for observable in relay_input:
        o_value = observable['value']
        o_type = observable['type'].lower()

        # Get only supported types by this third party
        if o_type in current_app.config['CCT_OBSERVABLE_TYPES']:
            obj = {'type': o_type, 'value': o_value}
            if obj in result:
                continue
            result.append(obj)
    return result

def build_input_api(observables):
    # formating, cleanup
    for observable in observables:
        o_value = observable['value']
        o_type = observable['type'].lower()
        if current_app.config['CCT_OBSERVABLE_TYPES'][o_type].get('sep'):
            o_value = o_value.split(
                current_app.config['CCT_OBSERVABLE_TYPES'][o_type]['sep'])[-1]
            observable['value'] = o_value
    return observables

enrich_api = Blueprint('enrich', __name__)
get_observables = partial(get_json, schema=ObservableSchema(many=True))

@enrich_api.route('/refer/observables', methods=['POST'])
def refer_observables():
    relay_input = get_json(ObservableSchema(many=True))
    observables = group_observables(relay_input)
    data = []
    if not observables:
        return jsonify_data({})
    observables = build_input_api(observables)
    for observable in observables:
        o_value = observable['value']
        o_type = observable['type'].lower()
        if o_type == 'ip':
            refer_url = 'https://isc.sans.edu/ipinfo.html?ip={}'.format(o_value)
            data.append(
                {
                    'id': 'ref-SANS-{}-{}'.format(o_type, o_value),
                    'title': f'Search for {o_value}',
                    'description': f'Look up {o_value} in SANS Internet Storm Center',
                    'url': refer_url,
                    'categories': ['Search', 'SANS']
                    }
                )
        else:
            return ({})
    return jsonify_data(data)

