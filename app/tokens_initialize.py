"""
initialize demo users and auth tokens
"""

# def create_all():

tokensdb = {'clientA_ba104cab58c17314' :'48a44d17902e960b8070a5f59eb5e02f',
                'clientB_555a79bdb472ead3':'7bb412f92c35a92923ccd178d45ff30c',
                '66666666666668':'d7811aa4852d7c021df3da133f8d3e11ad1e5c42d3ed0a1a',
                '66666666666661': 'd7811aa4852d7c021df3da133f8d3e11ad1e5c42d3ed0a1a'}

# undone - how to upload demo users to mongo?
for c in clients:
    c = User(username=myname,email=c+"@bar.com",
        password=v,
        clientid=k).save()
     
{
    "email":"aab@bob.com",
    "password":"asdfasdf",
    "clientId":"6666663"
}