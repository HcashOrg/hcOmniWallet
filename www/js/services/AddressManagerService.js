angular.module("omniServices")
	.service("AddressManager", ["$http", "TESTNET", function AddressManagerService($http, TESTNET){
		var self=this;
		self.validateAddress=function(addr) {
	      try {
	        var checkValid = new Bitcoin.Address(addr);
	        return true;
	      } catch (e) {
	        return false;
	      }
	    };
	    self.decodeAddressFromPrivateKey=function (key) {

	      //  Return the address decoded from the private key.
	      var eckey = new Bitcoin.ECKey(key);
	      var addr = eckey.getBitcoinAddress().toString();
	  
	      return addr;
	    };
	    self.encodePrivateKey=function(key, passphrase) {
	  
	      //  Return encoded key.  Forget the passphrase forever.
	      var eckey = new Bitcoin.ECKey(key);
	      var enc = eckey.getEncryptedFormat(passphrase);
	  
	      return enc;
	    };

	    self.createAddress = function () {
	      //var ecKey = new Bitcoin.ECKey();
	      //var address = ecKey.getBitcoinAddress().toString();
	      //var encryptedPrivateKey = ecKey.getEncryptedFormat(address);

	      //return {hash:address,privkey:encryptedPrivateKey}
              var bitcore = require("bitcore-lib");
              var privateKey = new bitcore.PrivateKey(null, TESTNET ? "hcdtestnet" : "hcdlivenet");
              return {hash:privateKey.toAddress().toString(), privkey:privateKey.toWIF()}
	    };

            self.estimateFee = function(address,btcAmount=null) {
              var url = '/v1/transaction/estimatefee/'+address;
              if (btcAmount==undefined) {
                return $http.get(url).then(function(response) {
                  return response;
                });
              } else {
		var postData = {
		  amountBTC: btcAmount
		};
                return $http.post(url, postData).then(function(response) {
                  return response;
                });
              }
            };

	    self.getTransactions = function(address) {
	    	var url = '/v1/transaction/address';
			var data = {
			  addr: address
			};
			//var promise = $http.post(url, data);
			//return promise;
			return $http.post(url, data).then(function(response) {
				return response;
			});
	    };
	}]);
