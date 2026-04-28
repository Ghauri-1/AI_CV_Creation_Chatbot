from dotenv import load_dotenv
import os

from openai import OpenAI


load_dotenv()


api_key=os.environ.get('CEREBRAS_API_KEY')


if not api_key:
    raise ValueError('The api key is non-foundable')

ini = OpenAI(
    api_key=os.getenv('OPENAI_API_KEY'),
    base_url='https://api.xiaomimimo.com/v1'
)

# init_model = ini.chat.completions.create()



if ini:
    print('Loaded Successfully !')


promp = input('Enter your prompt: ').lower()


while True:
    promp = input('Enter your prompt: ').lower()


    if promp not in ['quit', 'stop', 'exit']:
        
        chat_out = ini.chat.completions.create(
            messages=[
                {
                    'role':'user',
                    'content': promp
                }
            ],

            model='mimo-v2-flash'


        )

        print(chat_out.choices[0].message.content)
    else:
        print('Goodbye!!!')
        break
    'Hello!, who and what type of THING are you?'

