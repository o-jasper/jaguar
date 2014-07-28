;# Currency

{
  ;; Give caller a whole bunch of cash.
  [[ (caller) ]]: 0x1000000000000000000000000
  ;; Register with the NameReg contract.
  [0] "GavCoin"
  (call 0x929b11b8eeea00966e873a241d4b67f7540d1f38 0 0 0 7 0 0)

  (return 0 (lll {
    (when (!= (calldatasize) 64) (stop))      ; stop if there's not enough data passed.
    [fromBal] @@(caller)
    [toBal]: @@(calldataload 0)
    [value]: (calldataload 32)
    (when (< @fromBal @value) (stop))         ; stop if there's not enough for the transfer.
    [[ (caller) ]]: (- @fromBal @value)       ; subtract amount from caller's account.
    [[ (calldataload 0) ]]: (+ @toBal @value) ; add amount on to recipient's account.
  } 0))
}
