
# EVM code compiler

Recently forked off Serpent from when it was still written in python.
Nothing stable yet.

Intention, hope it is not too ambitious..:

* Add types. Usually this means deconstructing slots into parts. This is to save
  space on storage and transaction.
  + Arrays and structs.

* Variables. These use low indexes on on storage and memory.
  + Add `contract.some_var` or `.some_var` for short to automatically do slot
    creation on storage too. (obviously some are taken)
  + Have mechanisms for users to access memory themselves. Basically you can
    increment the current index at compile time in a scope.
      
* Try to get the names consistent between different EVM-targetting languages..
  Annoyingly serpent and LLL and others differ on this. 
