;#Name Registrar
;
;A simple name registeration service. Names (represented as 32-byte values
;whose left-most bytes store an ASCII string) are stored in the address space of
;the contract leading to the (160-bit ethereum) address of the name's owner. The
;owner addresses are similarly stored in the contract's address space with a
;value leading back to the name.

;; Initialiser...
{
  [[(address)]] "NameReg"
  [["NameReg"]] (address)
  [[69]] (caller)

  (return 0 (lll
    ;; If there's at least one argument
    (if (calldatasize)
      {
        ;; Stop if the first arg (name) has already been registered.
        (when @@(calldataload 0) (stop))

        ;; Store sender at name, and name at sender.
        (when @@(caller) [[@@(caller)]] 0)
        [[(calldataload 0)]] (caller)
        [[(caller)]] (calldataload 0)
        (stop)
      }

      ;; No arguments - either deregister or suicide (if it's from owner's address).
      {
        ;; Suicide if it's from owner's address.
        (when (= (caller) @@69) (suicide (caller)))

        ;; Otherwise, just deregister any name sender has, if they are registered.
        (when @@(caller) {
          [[@@(caller)]] 0
          [[(caller)]] 0
        })
        (stop)
      }
    )
  0))
}
