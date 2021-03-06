import simplejson
import requests
import decimal
import json, re
from config import BTAPIKEY
from rpcclient import gettxout
from cacher import *

try:
  expTime=config.BTCBAL_CACHE
except:
  expTime=600

def hc_getunspentutxo(address, ramount, avail=0):
  retval=[]
  try:
    r = requests.get('http://127.0.0.1:3006/api/addr/'+address+'/utxo?onCache=1')
    if r.status_code == 200:
      unspents = r.json()
      for tx in unspents:
        txUsed=gettxout(tx['txid'],tx['vout'])['result']
        isUsed = txUsed==None
        coinbaseHold = (txUsed['coinbase'] and txUsed['confirmations'] < 100)
        multisigSkip = ("scriptPubKey" in txUsed and txUsed['scriptPubKey']['type'] == "multisig")
        if not isUsed and not coinbaseHold and txUsed['confirmations'] > 0 and not multisigSkip:
          avail += tx['amount']*1e8
          retval.append(tx)
          if avail >= ramount:
            return {"avail": avail, "utxos": retval, "error": "none"}
      return {"avail": avail, "error": "Low balance error, account HC balance must be greater than " + str(ramount/1e8)}
    else:
      return {"error": "Connection error", "code": r.status_code}
  except Exception as e:
    return {"error": "Connection error", "code": e}

def bc_getbalance(address):
  try:
    balance=rGet("omniwallet:balances:address:"+str(address))
    balance=json.loads(balance)
    if balance['error']:
      raise LookupError("Not cached")
  except Exception as e:
    balance = bc_getbalance_explorer(address)
    #cache btc balance for 2.5 minutes
    rSet("omniwallet:balances:address:"+str(address),json.dumps(balance))
    rExpire("omniwallet:balances:address:"+str(address),expTime)
  return balance

def bc_getbalance_explorer(address):
  retval = {}
  try:
    r = requests.get('http://127.0.0.1:3006/api/addr/'+address+'/utxo?onCache=1')
    if r.status_code == 200:
      unspents = r.json()
      balance = 0
      for tx in unspents:
        txUsed=gettxout(tx['txid'],tx['vout'])['result']
        isUsed = txUsed==None
        coinbaseHold = (txUsed['coinbase'] and txUsed['confirmations'] < 100)
        multisigSkip = ("scriptPubKey" in txUsed and txUsed['scriptPubKey']['type'] == "multisig")
        if not isUsed and not coinbaseHold and txUsed['confirmations'] > 0 and not multisigSkip:
          balance += tx['amount']*1e8
      return {"bal":balance, "error": None}
    else:
      return {"bal":0, "error": r.status_code}
  except Exception as e:
    print e
    return {"bal":0, "error": e}

def bc_getbulkbalance(addresses):
  split=[]
  retval={}
  cbdata={}
  for a in addresses:
    try:
      cb=rGet("omniwallet:balances:address:"+str(a))
      cb=json.loads(cb)
      if cb['error']:
        raise LookupError("Not cached")
      else:
        cbdata[a]=cb['bal']
    except Exception as e:
      split.append(a)

  if len(split)==0:
    if len(cbdata) > 0:
      retval={'bal':cbdata, 'fresh':None}
    else:
      retval={'bal':{}, 'fresh':None}
  else:
    try:
      data=bc_getbulkbalance_explorer(split)
      if data['error']:
        raise Exception("issue getting explorer baldata",data)
      else:
        retval={'bal':dict(data['bal'],**cbdata), 'fresh':split}
    except Exception as e:
      print e

  rSetNotUpdateBTC(retval)
  return retval['bal']

def bc_getbulkbalance_explorer(addresses):
  retval = {}
  for address in addresses:
    retval[address] = bc_getbalance_explorer(address)["bal"]
  return {"bal": retval, "error": None}

# def bc_getpubkey(address):
#   try:
#     r = requests.get('https://blockchain.info/q/pubkeyaddr/'+address)

#     if r.status_code == 200:
#       return str(r.text)
#     else:
#       return "error"
#   except:
#     return "error"

# def bc_getutxo(address, ramount, avail=0):
#   retval=[]
#   try:
#     r = requests.get('http://192.168.186.138:3006/api/addr/'+address+'/utxo', verify=False)
#     if r.status_code == 200:
#       unspents = r.json()
#       for tx in unspents:
#         txUsed=gettxout(tx['txid'],tx['vout'])['result']
#         isUsed = txUsed==None
#         coinbaseHold = (txUsed['coinbase'] and txUsed['confirmations'] < 100)
#         multisigSkip = ("scriptPubKey" in txUsed and txUsed['scriptPubKey']['type'] == "multisig")
#         if not isUsed and not coinbaseHold and txUsed['confirmations'] > 0 and not multisigSkip:
#           avail += tx['amount']*1e8
#           retval.append([ tx['txid'], tx['vout'], tx['amount'] ])
#           if avail > ramount:
#             return {"avail": avail, "utxos": retval, "error": "none"}
#       return {"avail": avail, "error": "Low balance error"}
#     else:
#       return {"error": "Connection error", "code": r.status_code}
#   except Exception as e:
#     return {"error": "Connection error", "code": e}

# def bc_getutxo_blocktrail(address, ramount, page=1, retval=None, avail=0):
#   #deprecated and migrated to btc.com api
#   if retval==None:
#     retval=[]
#   try:
#     r = requests.get('https://api.blocktrail.com/v1/btc/address/'+address+'/unspent-outputs?api_key='+str(BTAPIKEY)+'&limit=200&sort_dir=desc&page='+str(page))
#     if r.status_code == 200:
#       response = r.json()
#       unspents = response['data']
#       print "got unspent list (btrail)", response
#       for tx in unspents:
#         txUsed=gettxout(tx['hash'],tx['index'])
#         isUsed = ('result' in txUsed and txUsed['result']==None)
#         coinbaseHold = (tx['is_coinbase'] and tx['confirmations'] < 100)
#         if not isUsed and not coinbaseHold and txUsed['result']['confirmations'] > 0 and tx['multisig']==None:
#           avail += tx['value']
#           retval.append([ tx['hash'], tx['index'], tx['value'] ])
#           if avail >= ramount:
#             return {"avail": avail, "utxos": retval, "error": "none"}
#       if int(response['total'])-(int(response['per_page'])*page ) > 0:
#         return bc_getutxo(address, ramount, page+1, retval, avail)
#       return {"avail": avail, "error": "Low balance error"}
#     else:
#       #return {"error": "Connection error", "code": r.status_code}
#       return bc_getutxo_blockcypher(address, ramount)
#   except:
#     return bc_getutxo_blockcypher(address, ramount)


# def bc_getutxo_blockcypher(address, ramount):
#   try:
#     r = requests.get('https://api.blockcypher.com/v1/btc/main/addrs/'+address+'?unspentOnly=true')

#     if r.status_code == 200:
#       unspents = r.json()['txrefs']
#       print "got unspent list (bcypher)", unspents

#       retval = []
#       avail = 0
#       for tx in unspents:
#         txUsed=gettxout(tx['tx_hash'],tx['tx_output_n'])
#         isUsed = ('result' in txUsed and txUsed['result']==None)
#         if tx['confirmations'] > 0 and not isUsed:
#           avail += tx['value']
#           retval.append([ tx['tx_hash'], tx['tx_output_n'], tx['value'] ])
#           if avail >= ramount:
#             return {"avail": avail, "utxos": retval, "error": "none"}
#       return {"avail": avail, "error": "Low balance error"}
#     else:
#       return {"error": "Connection error", "code": r.status_code}
#   except Exception as e:
#     if 'call' in e.message:
#       msg=e.message.split("call: ")[1]
#       ret=re.findall('{.+',str(msg))
#       try:
#         msg=json.loads(ret[0])
#       except TypeError:
#         msg=ret[0]
#       except ValueError:
#         #reverse the single/double quotes and strip leading u in output to make it json compatible
#         msg=json.loads(ret[0].replace("'",'"').replace('u"','"'))
#       return {"error": "Connection error", "code": msg['message']}
#     else: 
#       return {"error": "Connection error", "code": e.message}

# def bc_getbalance_bitgo(address):
#   try:
#     r= requests.get('https://www.bitgo.com/api/v1/address/'+address)
#     if r.status_code == 200:
#       balance = int(r.json()['confirmedBalance'])
#       return {"bal":balance , "error": None}
#     else:
#       return bc_getbalance_blockcypher(address)
#   except:
#     return bc_getbalance_blockcypher(address)

# def bc_getbalance_blockcypher(address):
#   try:
#     r= requests.get('https://api.blockcypher.com/v1/btc/main/addrs/'+address+'/balance')
#     if r.status_code == 200:
#       balance = int(r.json()['balance'])
#       return {"bal":balance , "error": None}
#     else:
#       return bc_getbalance_blockr(address)
#   except:
#     return bc_getbalance_blockr(address)

# def bc_getbalance_blockr(address):
#   try:
#     r= requests.get('http://btc.blockr.io/api/v1/address/balance/'+address)
#     if r.status_code == 200:
#       balance = int(r.json()['data']['balance']*1e8)
#       return {"bal":balance , "error": None}
#     else:
#       return {"bal": 0 , "error": "Couldn't get balance"}
#   except:
#       return {"bal": 0 , "error": "Couldn't get balance"}
      
# def bc_getbulkbalance_blockonomics(addresses):
#   formatted=""
#   for address in addresses:
#     if formatted=="":
#       formatted=address
#     else:
#       formatted=formatted+" "+address

#   try:
#     r = requests.post('https://www.blockonomics.co/api/balance',json.dumps({"addr":formatted}))
#     if r.status_code == 200:
#       balances = r.json()['response']
#       retval = {}
#       for entry in balances:
#         retval[entry['addr']] = int(entry['confirmed'])+int(entry['unconfirmed'])
#       return {"bal": retval, "error": None}
#     else:
#       return {"bal": None , "error": True}
#   except:
#     return {"bal": None , "error": True}

# def bc_getbulkbalance_blockr(addresses):
#   formatted=""
#   for address in addresses:
#     if formatted=="":
#       formatted=address
#     else:
#       formatted=formatted+","+address

#   try:
#     r= requests.get('http://btc.blockr.io/api/v1/address/balance/'+formatted)
#     if r.status_code == 200:
#       balances = r.json()['data']
#       retval = {}
#       for entry in balances:
#         retval[entry['address']] = int(entry['balance']*1e8)
#       return {"bal": retval, "error": None}
#     else:
#       return {"bal": None , "error": True}
#   except:
#     return {"bal": None , "error": True}

# def bc_getbulkbalance_blockchain(addresses):
#   formatted=""
#   for address in addresses:
#     if formatted=="":
#       formatted=address
#     else:
#       formatted=formatted+"|"+address
#   try:
#     r= requests.get('https://blockchain.info/balance?active='+formatted)
#     if r.status_code == 200:
#       balances = r.json()
#       retval = {}
#       for entry in balances:
#         retval[entry] = int(balances[entry]['final_balance'])
#       return {"bal": retval, "error": None}
#     else:
#       return {"bal": None , "error": True}
#   except:
#     return {"bal": None , "error": True}
