# xeno-canto API Wrapper
xeno-canto-py is an API wrapper designed to help users easily download xeno-canto.org recordings and associated information.

Originally created to aid in data collection and filtering for the training of machine learning models.
## Installation
Navigate to your desired file location in a terminal and then clone the repository with the following command:
```bash
git clone https://github.com/ntivirikin/xeno-canto-py
```
The only file required for operation is the ```xenocanto.py``` file, so feel free to remove the others or move ```xenocanto.py``` to another working directory.

You may also use the package manager [pip](https://pip.pypa.io/en/stable/) to install xeno-canto-py to include in your Python projects.

```bash
pip install xeno-canto
```
Then import the module:
```python
import xenocanto
```
Or use it straight from the command line:
```bash
xeno-canto -dl Bearded Bellbird
```
## Usage
Commands through the terminal are given in the following format:
```
-m 	[filters]	Metadata generation

-dl 	[filters] 	Download recordings

-d 	[filters]	Delete recordings

-p 	[num] 		Purge folders containing num or fewer recordings

-g 	[path] 		Generate metadata for provided library path (defaults to 'dataset/audio/')
```
```filters``` are given in tag:value form in accordance with the API search guidelines. For help in building search terms, consult the [xeno-canto API guide](https://www.xeno-canto.org/article/153). The only exception is when providing English bird names as an argument to the ```-d``` command, which must be preceded with ```en:``` and have all spaces be replaced with underscores.

Examples of command usage are given below:
```bash
# Retrieving metadata
xeno-canto -m Bearded Bellbird q:A

# Downloading recordings
xeno-canto -dl Bearded Bellbird cnt:Brazil

# Delete recordings with ANY of specified criteria from
# library
xeno-canto -d q:D cnt:Brazil

# Purge folders with less than 10 recordings
xeno-canto -p 10

# Generate metadata for all recordings in the path
# (defaults to 'dataset/audio/')
xeno-canto -g
```
## Contributing
All pull requests are welcome! If any issues are found, please do not hesitate to bring them to my attention.
## Acknowledgements
Thank you to the team at xeno-canto.org and all its contributors for putting together such an amazing database.
## License
[MIT](https://choosealicense.com/licenses/mit/)
