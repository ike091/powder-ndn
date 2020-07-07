#include <unistd.h>
#include <cstdlib>
#include <iostream>
#include <ndn-cpp/face.hpp>

using namespace std;
using namespace ndn;
using namespace ndn::func_lib;

class Counter {
       public:
	Counter() { callbackCount_ = 0; }

	void onData(const ptr_lib::shared_ptr<const Interest>& interest,
		    const ptr_lib::shared_ptr<Data>& data) {
		++callbackCount_;
		cout << "Got data packet with name " << data->getName().toUri()
		     << endl;
		for (size_t i = 0; i < data->getContent().size(); ++i)
			cout << (*data->getContent())[i];
		cout << endl;
	}

	void onTimeout(const ptr_lib::shared_ptr<const Interest>& interest) {
		++callbackCount_;
		cout << "Time out for interest " << interest->getName().toUri()
		     << endl;
	}

	int callbackCount_;
};

int main(int argc, char** argv) {
	try {
		// Silence warning from Interest wire encode
		Interest::setDefaultCanBePrefix(true);

		Face face("155.98.38.244");

		// Counter holds data used by callback
		Counter counter;

		Name name("/ndn/external/test");
		cout << "Express name " << name.toUri() << endl;
		// Use bind to pass the counter object to the callbacks

		face.expressInterest(name,
				     bind(&Counter::onData, &counter, _1, _2),
				     bind(&Counter::onTimeout, &counter, _1));

		while (counter.callbackCount_ < 1) {
			face.processEvents();

			usleep(10000);
		}

	} catch (std::exception& e) {
		cout << "exception: " << e.what() << endl;
	}
	return 0;
}

