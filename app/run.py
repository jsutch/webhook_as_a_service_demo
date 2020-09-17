if __name__ == '__main__':
    # without TLS
    app.run(host='0.0.0.0',port=6666, debug=True)
    # with TLS - need to uncomment the context head in imports
    # app.run(host='0.0.0.0',port=6666, debug=True, ssl_context=context)