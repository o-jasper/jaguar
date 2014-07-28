#!/bin/bash

lpimg()
{
    while read line; do 
        echo "<h4>$line</h4><img src=\"$line\">";
    done
}

echo "<h1>Shows off all the modes</h1>
Not really intended to be a good representation. You may have to zoom out to
see them well.

<h3>Control flow graphs of examples</h3>"
    
ls cf/cf_*.png | lpimg

echo "<h3>Straight graphs of examples</h3>
Goes straight from the graph. Largely not a useful graph. Nodes are made to be unique."
    
ls sg/sg_uniq_*.png | lpimg

echo "<h3>Straight graphs of examples, Not unique if name not unique</h3>
Even less useful for the former one, but looks different."

ls sg/sg_*.png | grep -v _uniq_ | lpimg

