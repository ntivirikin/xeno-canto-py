# xeno-canto API Wrapper

xeno-canto-py is an API wrapper designed to help users easily download xeno-canto.org recordings and associated information.

Originally created to aid in data collection and filtering for the training of machine learning models.

## Installation

Use the package manager [pip](https://pip.pypa.io/en/stable/) to install xeno-canto-py, or copy and paste the ```xenocanto.py``` file into your working directory.

```bash
pip install xeno-canto
```

## Usage

```get_json``` and ```get_mp3``` can be used to retrieve the JSON file and recordings from a query. Queries must be made according to the conventions detailed on the xeno-canto.org API search tips page found [here](https://www.xeno-canto.org/help/search).

The following commands will retrieve the query information for the genus *Otis* through ```get_json``` and then the recordings through ```get_mp3```. Both functions will return a list of file paths to the newly saved files for further use if required.

```python
import xenocanto


json_list = xenocanto.get_json(['gen:Otis'])
mp3_list = xenocanto.get_mp3(json_list)
```

```get_rec``` calls ```get_json``` with the provided query and immediately  calls ```get_mp3``` afterwards.

The following command will produce the same result as above.

```python
import xenocanto

xenocanto.get_rec(['gen:Otis'])
```

This will generate two folders, ```queries``` and ```recordings``` which will contain the JSON files with query data and recordings as MP3 files respectively.

The following will generate metadata in JSON form for machine learning models, assuming we are using the default recordings directory in the project folder. ```gen_meta``` will also accept a custom path if your recording library is located elsewhere.

```python
import xenocanto

xenocanto.gen_meta()
```

Metadata is saved to the local directory as ```metadata.json``` formatted as shown below.

```json
{["list":{"id":1, "label":value}]}
```
## Roadmap

* Add filtering of ```recordings``` folders (mainly by quality and background species)
* Add entrypoints for easier use

I am always open to suggestions for features!

## Contributing

All pull requests are welcome! If any issues are found, please do not hesitate to bring them to my attention.

## Acknowledgements

Thank you to the team at xeno-canto.org and all its contributors for putting together such an amazing database.

## License

[MIT](https://choosealicense.com/licenses/mit/)
