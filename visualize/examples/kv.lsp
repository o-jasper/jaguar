;# Key-Value Publisher

{
  [[69]] (caller)
  (return 0 (lll
    (when (= (caller) @@69)
      (for () (< @i (calldatasize)) [i](+ @i 64)
        [[ (calldataload @i) ]] (calldataload (+ @i 32))
      )
    )
  0))
}
