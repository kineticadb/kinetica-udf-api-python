<h3 align="center" style="margin:0px">
	<img width="200" src="https://www.kinetica.com/wp-content/uploads/2018/08/kinetica_logo.svg" alt="Kinetica Logo"/>
</h3>
<h5 align="center" style="margin:0px">
	<a href="https://www.kinetica.com/">Website</a>
	|
	<a href="https://docs.kinetica.com/7.2/">Docs</a>
	|
	<a href="https://docs.kinetica.com/7.2/udf/python/writing/">UDF API Docs</a>
	|
	<a href="https://join.slack.com/t/kinetica-community/shared_invite/zt-1bt9x3mvr-uMKrXlSDXfy3oU~sKi84qg">Community Slack</a>   
</h5>


# Kinetica Python UDF API

-  [Overview](#overview)
-  [API](#api)
-  [Example](#example)
-  [Apache Arrow](#apache-arrow)
-  [UDF Reference Documentation](#udf-reference-documentation)
-  [Support](#support)
-  [Contact Us](#contact-us)


## Overview

This is the 7.2 version of the server-side Python UDF API for Kinetica.  UDFs
are server-side programs written in this API and then installed, configured, and
initiated through a separate client-side management API.  These two APIs are
independent of each other and do not need to be written in the same language;
e.g., a UDF can be written in the Python UDF API and managed in SQL (from
Workbench, KiSQL, or other database client).

The source code for this project can be found at
https://github.com/kineticadb/kinetica-udf-api-python

For changes to the client-side API, please refer to
[CHANGELOG.md](CHANGELOG.md).


## API

This repository contains the Kinetica Python UDF API solely contained in the
`kinetica-proc.py` file.

This file will be available within the server environment and can be imported
into the UDF as follows:

    from kinetica_proc import ProcData


## Example

This repository also contains several example projects in the `examples`
directory, which implement UDFs in the Python UDF API.


## Apache Arrow

The Kinetica Python UDF API supports Apache Arrow natively. A few examples
that demonstrate using Apache Arrow with Kinetica are available:

* [UDF Distributed Model](https://github.com/kineticadb/kinetica-udf-api-python/tree/master/examples/UDF_distributed_model)
* [UDF H2O Generalized Linear Model](https://github.com/kineticadb/kinetica-udf-api-python/tree/master/examples/UDF_h2o_glm)
* [UDF H2O Random Forest Model](https://github.com/kineticadb/kinetica-udf-api-python/tree/master/examples/UDF_h2o_rf)


## UDF Reference Documentation

For information about UDFs in Kinetica, please see the User-Defined Functions
sections of the Kinetica documentation:

* **UDF Concepts**:  https://docs.kinetica.com/7.2/udf_overview/
* **Python UDF API**:  https://docs.kinetica.com/7.2/udf/python/writing/
* **Python UDF Management API**:  https://docs.kinetica.com/7.2/udf/python/running/
* **Python UDF Tutorial**:  https://docs.kinetica.com/7.2/guides/udf_python_guide/
* **Python UDF Examples**:  https://docs.kinetica.com/7.2/udf/python/examples/


## Support

For bugs, please submit an
[issue on Github](https://github.com/kineticadb/kinetica-udf-api-python/issues).

For support, you can post on
[stackoverflow](https://stackoverflow.com/questions/tagged/kinetica) under the
``kinetica`` tag or
[Slack](https://join.slack.com/t/kinetica-community/shared_invite/zt-1bt9x3mvr-uMKrXlSDXfy3oU~sKi84qg).


## Contact Us

* Ask a question on Slack:
  [Slack](https://join.slack.com/t/kinetica-community/shared_invite/zt-1bt9x3mvr-uMKrXlSDXfy3oU~sKi84qg)
* Follow on GitHub:
  [Follow @kineticadb](https://github.com/kineticadb) 
* Email us:  <support@kinetica.com>
* Visit:  <https://www.kinetica.com/contact/>
