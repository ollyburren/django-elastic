import os
from setuptools import setup, find_packages

# with open(os.path.join(os.path.dirname(__file__), 'README.rst')) as readme:
#     README = readme.read()

# allow setup.py to be run from any path
os.chdir(os.path.normpath(os.path.join(os.path.abspath(__file__), os.pardir)))
ROOT = os.path.abspath(os.path.dirname(__file__))

setup(
    name='elastic',
    version='0.0.1',
    packages=find_packages(),
    package_data={'elastic': ['tests/data/*gz',
                              'tests/data/*json',
                              'tests/data/*bed',
                              'tests/data/alias_test_dir/gene_alias/*',
                              'tests/data/alias_test_dir/locus_alias/*',
                              'tests/data/alias_test_dir/marker_alias/*',
                              'tests/data/alias_test_dir/study_alias/*'], },
    include_package_data=True,
    zip_safe=False,
    url='http://github.com/D-I-L/django-elastic',
    description='A Django app to run and view Elastic elastic queries.',
    long_description=open(os.path.join(ROOT, 'README.rst')).read(),
    install_requires=["requests>=2.7.0", "Django>=1.8.4,<1.9", "djangorestframework>=3.2.4",
                      "markdown>=2.6.2", "django-filter>=0.11.0", "django-rest-swagger==0.3.4"],
    classifiers=[
        'Environment :: Web Environment',
        'Framework :: Django',
        'Intended Audience :: Developers',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3.4',
        'Topic :: Internet :: WWW/HTTP',
        'Topic :: Internet :: WWW/HTTP :: Dynamic Content',
    ],
)
