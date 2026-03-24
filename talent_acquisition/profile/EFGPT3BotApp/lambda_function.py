import json
import requests

ICON_native = 'https://openai.com/favicon.png'
ICON1 = 'https://cdn3.iconfinder.com/data/icons/artificial-intelligence-ai-glyph/64/openai-gym-Toolkit-algorithm-Reinforcement-Learning_-512.png'

DEFAULT_MODEL_PARAMS = {
    "max_tokens": 100,
    "temperature": 0.8,
    "top_p": 1,
    "n": 1,
    "stream": False,
    "logprobs": None,
    "best_of": 1
}

def _call_gpt(prompt, model_params, api_key):
    print('prompt: {}'.format(prompt))
    headers = {
        'Content-Type': 'application/json',
        'Authorization': 'Bearer {}'.format(api_key),
    }
    model_params = model_params or DEFAULT_MODEL_PARAMS
    model_params['prompt'] = prompt

    print('gpt_request: {}'.format(model_params))
    gpt_resp = requests.post('https://api.openai.com/v1/engines/davinci-instruct-beta/completions',
                                 headers=headers,
                                 data=json.dumps(model_params))
    print('gpt_response: {}'.format(gpt_resp.content))

    return gpt_resp


def app_handler(event, context):
    if event.get('trigger_name') == 'ta_profile_view':
        request_data = event.get('request_data', {})
        print('request_data: {}'.format(request_data))

        title = request_data.get('title').split(',')[0]
        skills = ", ".join(request_data.get('skills')[:4]) or ""

        app_settings = event.get('app_settings', {})
        print('app_settings: {}'.format(app_settings))


        preprompt = app_settings.get('preprompt') or "Interview questions for"
        prompt = app_settings.get('prompt') or "{} {}".format(preprompt, title)

        gpt_resp = _call_gpt(prompt, app_settings.get('model_params'), app_settings.get('api_key'))

        resp_text = ''
        if gpt_resp.status_code == 200:
            gpt_resp_json = json.loads(gpt_resp.content)
            resp_text = gpt_resp_json.get('choices')[0].get('text')

        resp_text = resp_text.replace('\\n\\n', '')
        resp_text = resp_text[0:resp_text.rfind('?')+1].strip()
        questions = [r+'?' for r in resp_text.split('?') if r]

        rows = [[{'value': q, 'link': ""}] for q in questions]

        data = {
            'title': 'Suggested Conversations',
            'subtitle': 'Interview questions for {}'.format(title),
            'logo_url': ICON1,
            'tiles': [],
            'table': {
                'headers': [''],
                'rows': rows
            }
        }
        print('app_resp: {}'.format(data))
        return {
            'statusCode': 200,
            # 'body': json.dumps({'html': render_html.format(all_choices)})
            # 'body': json.dumps({'data': data, 'template': 'app_platform/ef_career_hub_profile_module.html'})
            'body': json.dumps({'data': data})
        }
