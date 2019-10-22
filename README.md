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

## Usage
Commands through the terminal are given in the following format:
```bash
python3 xenocanto.py -action args
```
Possible actions and their required inputs:
```
-m			Metadata generation
-dl			Download recordings
-d			Delete recordings based on 
-p	[num]	Purge folders containing num or fewer 
			recordings
-g	[path]	Generate metadata for provided library path 
			(defaults to 'dataset/audio/')
```
For help in building search terms, consult the [xeno-canto API guide](https://www.xeno-canto.org/article/153).

Example of a workflow is given below with comments:
```bash
# Downloading all the metadata for recordings with 
# 'gen' equal to 'Otis'
python3 xenocanto.py -m gen:Otis
```
## Contributing
All pull requests are welcome! If any issues are found, please do not hesitate to bring them to my attention.

## Acknowledgements
Thank you to the team at xeno-canto.org and all its contributors for putting together such an amazing database.

## License
[MIT](https://choosealicense.com/licenses/mit/)