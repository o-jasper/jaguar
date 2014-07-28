;# Bank
;
;A very simple bank. You can send ether in a transaction to load your account
;with funds. Withdraw your ether by specifying a 32-byte data argument of the
;amount to withdraw. Withdraw to a different account by specifying a second data
;argument with the account.

{
  [0] "Bank"
  (call 0x929b11b8eeea00966e873a241d4b67f7540d1f38 0 0 0 4 0 0)

  (return 0 (lll {
    (if (>= @@(caller) (calldataload 0))
      ;; Withdrawal:
      {
        ;; Subtract the value from the balance of the account
        [[ (caller) ]] (- @@(caller) (calldataload 0))
        ;; Transfer the funds either to...
        (if (<= (calldatasize) 32)
          (call (- (GAS) 100) (caller) (calldataload 0) 0 0 0 0)  ; ...the sender...
          (call (- (GAS) 100) (calldataload 32) (calldataload 0) 0 0 0 0)  ; ...or the supplied account.
        )
      }
      ;; Deposit; just increase the account balance by that amount.
      [[(caller)]] (+ @@(caller) (callvalue))
    )
  } 0))
}
