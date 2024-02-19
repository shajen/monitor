#!/bin/bash

function gen_decoder {
    python_file="${1%.*}.py"
    rm $python_file
    tmp_file=tmp.txt
    grcc $1
    sed "s/__init__(self)/__init__(self, in_file, out_file, sample_rate)/g" $python_file > $tmp_file && mv $tmp_file $python_file
    sed "s/'tmp.wav'/out_file/g" $python_file > $tmp_file && mv $tmp_file $python_file
    sed "s/'tmp.raw'/in_file/g" $python_file > $tmp_file && mv $tmp_file $python_file
    sed "s/self\.sample_rate =.*/self.sample_rate = sample_rate/g" $python_file > $tmp_file && mv $tmp_file $python_file
}

pushd sdr/decoders
gen_decoder fm_decoder.grc
gen_decoder am_decoder.grc
popd
