#!/usr/bin/env python
# This program is dedicated to the public domain under the CC0 license.

"""
A Telegram bot that answer questions about a document: in this example guidelines of the "Geneva Hospice General".  

First, a few handler functions are defined. Then, those functions are passed to
the Application and registered at their respective places.
Then, the bot is started and runs until we press Ctrl-C on the command line.

"""

import logging

import os

from google.cloud import translate_v2 as translate

os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = "/path/to/your/google_cloud_translate_credentials.json"

def translate_to_ukrainian(text):
    translate_client = translate.Client()
    target = 'uk'  # 'uk' is the language code for Ukrainian
    translation = translate_client.translate(text, target_language=target) 
    return translation['translatedText']

from langchain.embeddings.openai import OpenAIEmbeddings
from langchain.vectorstores import Chroma
#from langchain.text_splitter import CharacterTextSplitter
from langchain.chains import ChatVectorDBChain

from langchain.chat_models import ChatOpenAI  
from langchain.prompts.chat import (
    ChatPromptTemplate,
    SystemMessagePromptTemplate,
    AIMessagePromptTemplate,
    HumanMessagePromptTemplate,
)

# Set up logging configuration
logging.basicConfig(filename='telegram-bot.log', encoding='utf-8', level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# this is your OpenAI api-key!
api_key = "HereGoesYourOpenAIapi-key"

# this is your Telegram api-key
TOKEN = '12345:HereGoesYourTELEGRAMapi-key'


#########################################################################################################################
# This is where the magic happens: the Hospice General info document
# "Hospice_General_Directives_version_validee_DSE.pdf" has been previously converted to semantic vectors. 
# For more info, see here: https://python.langchain.com/en/latest/modules/indexes.html
# and, more technically here: https://python.langchain.com/en/latest/modules/indexes/vectorstores/examples/chroma.html
# These semantic vectors are now loaded into memory from the "vectorstore".
#########################################################################################################################


persist_directory = "/home/path/to/your_vectorbase/"  
embeddings = OpenAIEmbeddings(openai_api_key=api_key)

vectorstore = Chroma(persist_directory=persist_directory, embedding_function=embeddings)

# CHAT_GPT API following

system_template="""Ви корисний, доброзичливий мовний зразок, навчений інформації про Женевський хоспіс. Оскільки вашими користувачами будуть українські біженці, ви намагатиметеся відповідати на всі запитання українською мовою.
Використовуйте наступні частини контексту, щоб відповісти на запитання користувача.
Якщо ви не знаєте відповіді, просто скажіть, що не знаєте, не намагайтеся вигадати відповідь.
Якщо користувач запитує про щось інше, ніж те, що описано у фрагментах контексту, ввічливо скажіть, що ви можете допомогти лише з питаннями Женевського хоспісу.
Будь ласка, спробуйте відповісти дуже простою, зрозумілою мовою.

ЦЕ НАДЗВИЧАЙНО ВАЖЛИВО: ВАШІ КОРИСТУВАЧІ НЕ РОЗУМІЮТЬ АНГЛІЙСЬКОЇ АБО ФРАНЦУЗЬКОЇ МОВИ. ВАШІ КОРИСТУВАЧІ РОЗУМІЮТЬ ТІЛЬКИ УКРАЇНСЬКУ. ТОМУ ВИ ВІДПОВІДАЄТЕ ТІЛЬКИ УКРАЇНСЬКОЮ!
--------------
{context}"""
messages = [
    SystemMessagePromptTemplate.from_template(system_template),
    HumanMessagePromptTemplate.from_template("{question}")
]
prompt = ChatPromptTemplate.from_messages(messages)

qa = ChatVectorDBChain.from_llm(ChatOpenAI(openai_api_key=api_key, temperature=0), vectorstore, qa_prompt=prompt)

chat_history = []
result = {}
result["answer"] = ""
last_question = ""

def respond_to(text):
  global chat_history
  global result
  global last_question
  chat_history = [(last_question, result["answer"])]
  result = qa({"question": text, "chat_history": chat_history})
  response = str(result["answer"])
  last_question = text
  return response

import re

def has_less_than_4_ukrainian_letters(string):
    """This function tests if a string has less than 4 ukrainian letters,
    - which indicates that the string has NOT YET been translated into Ukrainian. 
    """
    ukrainian_alphabet_pattern = re.compile('[А-ЩЬЮЯҐЄІЇа-щьюяґєії]')
    ukrainian_letters_count = len(ukrainian_alphabet_pattern.findall(string))
    return ukrainian_letters_count < 4

def replace_html_entities(text):
    text2 = text.replace("&#39;", "'")
    text3 = text2.replace("&quot;", '"')
    return text3


# TELEGRAM loop starts here

from telegram import __version__ as TG_VER

try:
    from telegram import __version_info__
except ImportError:
    __version_info__ = (0, 0, 0, 0, 0)  # type: ignore[assignment]

if __version_info__ < (20, 0, 0, "alpha", 1):
    raise RuntimeError(
        f"This example is not compatible with your current PTB version {TG_VER}. To view the "
        f"{TG_VER} version of this example, "
        f"visit https://docs.python-telegram-bot.org/en/v{TG_VER}/examples.html"
    )
from telegram import ForceReply, Update
from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, filters

# Define a few command handlers. These usually take the two arguments update and
# context.

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a message when the command /start is issued."""
    user = update.effective_user
    await update.message.reply_html(
        rf"Bonjour {user.mention_html()}! Привіт. Якщо у вас виникнуть будь-які запитання щодо Geneva Hospice General, можливо, я зможу вам допомогти. Ви б хотіли мене щось запитати?",
        reply_markup=ForceReply(selective=True),
    )
    logging.info(f"User {user.mention_html()} started a conversation with the bot.")

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a message when the command /help is issued."""
    await update.message.reply_text("Help!")

info_text =  "Цей бот надає деяку інформацію про Geneva Hospice General. Однак це НЕ офіційний бот, і його інформацію слід перевірити, звернувшись до Hospice General. https://www.hospicegeneral.ch/fr"

async def info_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a message when the command /info is issued."""
    await update.message.reply_text(info_text)


async def my_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """RESPOND VIA GPT to the user message."""
    input_message = update.message.text
    user = update.effective_user
    logging.info(f"User {user.mention_html()} sends: {input_message}")
    output_message = respond_to(input_message)
    if has_less_than_4_ukrainian_letters(output_message):
        logging.info(f"TRANSLATION NECESSARY...Bot responds: {output_message}")
        ukrainian_output = translate_to_ukrainian(output_message)
        output_message = replace_html_entities(ukrainian_output) #ukrainian_output.text

    await update.message.reply_text(output_message)
    logging.info(f"Bot responds: {output_message}")

    
def main() -> None:
    """Start the bot."""

    # Create the Application and pass it your bot's token.ls
    application = Application.builder().token(TOKEN).build()

    # on different commands - answer in Telegram
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("info", info_command))

    # on non command i.e message - echo the message on Telegram
    #application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, echo))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, my_handler))

    # Run the bot until the user presses Ctrl-C
    application.run_polling()


if __name__ == "__main__":
    main()
