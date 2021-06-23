NFSv4-SHARE
===========

## Installation
Using PyPi:

```
pip install nfs4_share
```      

Or install from source:
1. clone the repository
2. `cd` into the repository directory
3. Install using:

            pip install .


## Usage:

Run `nfs4_share --help` for arguments. A more detailed description can be found [below](#practical_example)

## Motivation
Typically Within the high-performance clusters a bulkstorage is exposed as a mount with type Network Filestorage System 
version 4 (NFSv4). To protect the data only limited read access is granted and to an even lesser degree write access is 
granted. Playing safe can become a problem when the need arises to share the results with other researchers members. Manually 
providing and revoking access on an NFSv4 is possible but cumbersome and error prone. Simply copying the data to a shared 
location is dangerous and very quickly increases usage of expensive storage. This can be very expensive.

The NFSv4-SHARE program is build to solve this problem. It uses properties of the NFSv4 mount to prevent *data 
duplication* and makes keeping track of permissions relatively easy. Data duplication is prevented by only creating
 [hard-links to files](https://esc.sh/blog/inode-hardlink-softlink-explained/). Keeping track of permissions is done by 
 wrapping the hard-linked files in a directory that all share the same permissions.

Access to the data and shares itself is controlled by [NFSv4 access-control lists (ACLists)](https://linux.die.net/man/5/nfs4_acl). 
These ACLists consist of entries (ACEntries) which determine what permissions a calling user has. The main differences 
between ACLists and the standard POSIX permissions (i.e. `rwxrwxrwx`) are as follows:

* multiple users and groups can be defined
* more fine-grained permissions can be controlled (13 for files, 14 for directories).

A small addition has been made to also control the `.htaccess` file of a share to allow data sharing via an apache server.

------------------------------------------------------------------


## Practical Example
Take some imaginary source data that is structured as follows:

		/data/results/
				QC.txt
		/raw_data/sample1/
				run_L1.bam
				run_L2.bam
		/shares/..

If you want to do the following:

* create a share for project `foobar` under `/shares`
* share the file `QC.txt` from directory `/data/results`
* share the subdirectory `sample1/` from directory `/raw_data`
* provide access to user `bob` and `alice`
* manage the share with group `pmc_omics`

You run the following command:

		nfs4_share create /shares/foobar \
		--users bob alice \
		--managing_groups pmc_omics \
		--items /data/results/QC.txt /raw_data/sample1


You then end up with a share and source data that is structured as follows:

		/data/results/
				QC.txt
		/raw_data/sample1/
				run_L1.bam
				run_L2.bam
		/shares/foobar/
				QC.txt
				sample1/
					run_L1.bam
					run_L2.bam

Users `bob` and `alice` could then navigate to the share at `/shares/foobar` to access the shared data.

When they finish or you need to recreate the share, use NFSv4-SHARE to delete the share:

		nfs4_share delete /shares/foobar

## Implementation Details

The ACLists on the share directory (i.e. `/shares/foobar`) are the _de facto_ share permissions.

### Shared Files
Within the example above, all the _files_ have the original ACEntries. These NEED to include reading permissions.

### Shared Directories
Any _subdirectories_ from the source that end up in foobar are **different subdirectories(!)**. The directories from 
the specified source items have their tree freshly rebuild within the share. For instance, the directory `/shares/foobar/sample1` 
is not a hard-link to `/raw_data/sample1`, but a remake. The directories share the name `sample1` but have a different 
inode number and associated ACList. Within the `foobar` share, the ACList of directory `sample1`  only has the ACEntries 
required to have bob and alice read and index files.

## Unit tests
If the source code is located on an NFSv4 mount with ACLs enabled you can run unit tests as follows:
        
```bash
pip install .[test]
pytest --basetemp=<NFS4_MOUNT>
```

If the source code is not stored on an NFSv4 mount, you should first move it to an NFSv4 mount before unit testing.

Luckily, this is already automated in the following script. It will push the source code to the remote server and have the
unittest runs there locally.
```bash
bash tests/run_test_on_remote_server.sh <ssh_remote_host> <remote_working_directory> <remote_nfs4_mount_for_creating_shares> <test_variables.json>
```
example: bash tests/run_test_on_remote_server.sh gwhorus test_shares_exc /data/isi/p/pmc_research/omics/development/shares tests/variables_UMC.json

In case you are working on a cripled OS lacking the "realpath" function then use run_test_on_remote_server_mac.sh

      
      
## Python Module Interface
If you want to programmatically call this program within python you can use something as follows:
```python
from nfs4_share.manage import create, delete

create(share_directory="/data/isi/p/pmc_research/omics/shares/share1",
                domain="op.umcutrecht.nl",
                items=["file1.txt", "file2.txt"])
                
delete(share_directory="/data/isi/p/pmc_research/omics/shares/share1")

```

## Upload new version to PyPi
This requires an account at [pypi.org](pypi.org) with access to the [project]().

1. Change the version number in `./__version__.py`
2. Tag a new version 

        git tag v0.1.0
3. Install required packages for uploading

        pip install --upgrade setuptools wheel twine
4. Build dist

        python setup.py sdist bdist_wheel
5. Upload using `twine`

        twine upload dist/*
