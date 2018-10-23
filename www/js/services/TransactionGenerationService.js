angular.module('omniServices')
  .service('TransactionGenerator',['$http',"TESTNET","SATOSHI_UNIT",function TransactionGeneratorService($http, TESTNET, SATOSHI_UNIT){
    var self = this;
      self.pushSignedTransaction = function(signedTransaction) {
        var url = '/v1/transaction/pushtx/';
        var data = {
          signedTransaction: signedTransaction
        };
        var promise = $http.post(url, data);
        return promise;
      };
      
      self.getUnsignedTransaction = function(type, data){
        if (type == 0 && data.currency_identifier == 0){ // BTC send
          d = {
            'from_address':data.pubkey,
            'to_address':data.transaction_to,
            'amount':new Big(data.amount_to_transfer).times(SATOSHI_UNIT).valueOf(),
            'currency':'BTC',
            'fee':data.fee,
            'marker': (data.marker || false),
            'testnet': (TESTNET || false)
          };
          if(data.transaction_from && data.transaction_from.length > 0){
            d['from_address'] = data.transaction_from;
            d['pubkey'] = data.pubkey;
	  }
          var url = '/v1/transaction/send/';
          var promise = $http.post(url, d);
          return promise;
        } 
        // SP and simple send tx
        var url = '/v1/transaction/getunsigned/'+type;
        var promise = $http.post(url, data);
        return promise;
         
      },

      self.getArmoryUnsigned = function(unsignedHex,pubKey){
        var url = '/v1/armory/getunsigned';
        var data = {
          'unsigned_hex': unsignedHex,
          'pubkey': pubKey
        };
        var promise = $http.post(url, data);
        return promise;
      },
      
      self.getArmoryRaw = function(signedHex){
        var url = '/v1/armory/getrawtransaction';
        var data = {
          'signed_hex': signedHex
        };
        var promise = $http.post(url, data);
        return promise;
      }
    }]);
