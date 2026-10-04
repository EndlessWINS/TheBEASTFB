import uvicorn,os; uvicorn.run('api.server:app',host='0.0.0.0',port=int(os.getenv('PORT',10000)))
