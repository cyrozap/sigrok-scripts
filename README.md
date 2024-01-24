# sigrok-scripts

Miscellaneous scripts for generating and processing [sigrok][sigrok] data files.

* [sr-i2c-to-txt.sh](sr-i2c-to-txt.sh): A shell script for decoding sigrok
  captures of I2C transactions.
* [waveforms-csv-to-sr.py](waveforms-csv-to-sr.py): A Python script for
  converting [Digilent WaveForms][waveforms] "Raw Data" format CSV files to
  sigrok's [srzip][srzip] (`.sr`) format.


## License

Except where stated otherwise, the contents of this repository are released
under the [Zero-Clause BSD (0BSD) license][license].


[sigrok]: https://sigrok.org/
[waveforms]: https://digilent.com/reference/software/waveforms/waveforms-3/start
[srzip]: https://sigrok.org/wiki/File_format:Sigrok/v2
[license]: LICENSE.txt
