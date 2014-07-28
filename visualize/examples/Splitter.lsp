;# Splitter
;
;Simple cash splitter; splits the value sent amongst each of the addresses given
;as data items.

{
  [0] "Splitter"
  (call 0x929b11b8eeea00966e873a241d4b67f7540d1f38 0 0 0 8 0 0)

  (return 0 (lll {
    [count] (/ (calldatasize) 32)
    [pay] (/ (callvalue) @count)

    ;; Cycle through each address
    (for () (< @i @count) [i](+ @i 1)
      ;; Send to 'i'th argument (assuming it's an address).
      (call (- (GAS) 100) (calldataload (* @i 32)) @pay 0 0 0 0)
    )
  } 0))
}
