Design
==============

The design of the Kafka Monitor stemmed from the need to define a format that allowed for the creation of crawls in the crawl architecture from any application. If the application could read and write to the kafka cluster then it could write messages to a particular kafka topic to create crawls.

Soon enough those same applications wanted the ability to retrieve and stop their crawls from that same interface, so we decided to make a dynamic interface that could support all of the request needs, but utilize the same base code. In the future this base code could expanded to handle any different style of request, as long as there was a validation of the request and a place to send the result to.

From our own internal debugging and ensuring other applications were working properly, a utility program was also created on the side in order to be able to interact and monitor the kafka messages coming through. This dump utility can be used to monitor any of the Kafka topics within the cluster.