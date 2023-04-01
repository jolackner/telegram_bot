# A Minimalist Telegram Bot for Document Queries

A simple Telegram Bot (which can be hosted on Pythonanywhere) that answers questions on this document by the Geneva Hospice General: 
https://www.hospicegeneral.ch/sites/default/files/Directives_version_validee_DSE.pdf  
It tries to answer any question on this topic in Ukrainian.  

NOTE/DISCLAIMER: this is NOT an official bot by the Hospice General. Any info you take from this bot should be confirmed directly by getting in contact with the Hospice General. 

In order to host this or a similar bot, you need:
- an OpenAI account and token
- a Telegram account and token
- (optionally) a Google Translate account and credentials
- a hosting platform that can serve the bot, for example on [Pythonanywhere](https:www.pythonanywhere.com).

This bot makes use of the wonderful  [LangChain framework](https://python.langchain.com/en/latest/index.html)   
It takes advantage of the [python telegram-bot wrapper](https://github.com/python-telegram-bot/python-telegram-bot)   
The code has been adapted from [this](https://github.com/python-telegram-bot/python-telegram-bot/blob/master/examples/echobot.py) template.





