angular.module("omniServices")
    .service("TransactionManager", ["$q", "TESTNET", "SATOSHI_UNIT", "TransactionGenerator", "TX_DATA_URL",
        function TransactionManagerFactory($q, TESTNET, SATOSHI_UNIT, TransactionGenerator, TX_DATA_URL) {

            var self = this;

            self.parseScript = function(script) {
                var newScript = new Bitcoin.Script();
                var s = script.split(" ");
                for (var i = 0; i < s.length; i++) {
                    if (Bitcoin.Opcode.map.hasOwnProperty(s[i])) {
                        newScript.writeOp(Bitcoin.Opcode.map[s[i]]);
                    } else {
                        newScript.writeBytes(Bitcoin.Util.hexToBytes(s[i]));
                    }
                }
                return newScript;
            }

            self.prepareTransaction = function(unsignedTransactionHex, sourceScript) {

                var bytes = Bitcoin.Util.hexToBytes(unsignedTransactionHex);
                var transaction = Bitcoin.Transaction.deserialize(bytes);
                //var script = self.parseScript(sourceScript);

                if (transaction.ins.length == 0) {
                    return {
                        waiting: false,
                        transactionError: true,
                        error: 'Error: Not enough inputs in the address!'
                    };
                }
                transaction.ins.forEach(function(input) {
                    if (typeof(sourceScript) == typeof("string")) {
                      var script = sourceScript;
                    } else {
                      var sl = input['outpoint']['hash'] + ":" + input['outpoint']['index'];
                      var script = sourceScript[sl];
                    }
                    input.script = self.parseScript(script);
                });
                return transaction;
            }

            self.processTransaction = function(transaction) {
                console.log()
                var deferred = $q.defer();
                TransactionGenerator.getUnsignedTransaction(transaction.type, transaction.data).then(
                    function(successData) {
                        var successData = successData.data;
                        if (successData.status != 200 && successData.status != "OK") { /* Backwards compatibility for mastercoin-tools send API */
                            deferred.reject({
                                waiting: false,
                                transactionError: true,
                                error: successData.error || successData.data, /* Backwards compatibility for mastercoin-tools send API */
                                errorMessage: successData.error || "Error preparing transaction"
                            });
                        } else {
                            var bitcore = require("bitcore-lib");
                            var privateKey = bitcore.PrivateKey(transaction.address.privkey, TESTNET ? "hcdtestnet" : "hcdlivenet");
                            var fee = new Big(transaction.data.fee).times(SATOSHI_UNIT).valueOf();
                            if (transaction.type == 0 && transaction.data.currency_identifier == 0){
                                var amount = new Big(transaction.data.amount_to_transfer).times(SATOSHI_UNIT).valueOf();
                                var finalTransaction = bitcore.Transaction()
                                                        .from(successData.utxos)
                                                        .to(transaction.data.transaction_to, Math.floor(amount))
                                                        .fee(Math.floor(fee))
                                                        .change(transaction.data.transaction_from)
                                                        .sign(privateKey);
                            } else {
                                var firstOutputAddr = transaction.data.transaction_to == undefined ? transaction.data.transaction_from : transaction.data.transaction_to;
                                var payload = bitcore.util.buffer.hexToBuffer("6f6d6e69"+successData.payload);
                                var finalTransaction = bitcore.Transaction()
                                                        .from(successData.utxos)
                                                        .to(firstOutputAddr, 100000)
                                                        .addData(payload)
                                                        .fee(Math.floor(fee))
                                                        .change(transaction.data.transaction_from)
                                                        .sign(privateKey)
                            }
                            TransactionGenerator.pushSignedTransaction(finalTransaction.toString()).then(
                                function(successData) {
                                    var successData = successData.data;
                                    if (successData.pushed.match(/submitted|success/gi) != null) {
                                        deferred.resolve({
                                            waiting: false,
                                            transactionSuccess: true,
                                            url : TX_DATA_URL + successData.tx
                                        })
                                    } else if (successData.status.match(/NOTOK/gi)) {
                                        deferred.reject({
                                            waiting: false,
                                            transactionError: true,
                                            error: successData.pushed, //known error, show user
                                            errorMessage: successData.pushed+" Reason: "+successData.message
                                        })
                                    } else {
                                        deferred.reject({
                                            waiting: false,
                                            transactionError: true,
                                            error: successData.pushed, //Unspecified error, show user
                                            errorMessage: "Invalid transaction"
                                        })
                                    }
                                },
                                function(errorData) {
                                    //console.log(errorData);
                                    deferred.reject({
                                        waiting: false,
                                        transactionError: true,
                                        error: errorData.message || errorData.data || 'Unknown Server Error',
                                        errorMessage:'Server error'
                                    })
                                }
                            );
                        }
                    },
                    function(errorData) {
                        deferred.reject({
                            sendError: true,
                            error: errorData.message || errorData.data || 'Unknown Server Error',
                            errorMessage:'Server error'
                        })
                    });
                return deferred.promise;
            };

    }]);
