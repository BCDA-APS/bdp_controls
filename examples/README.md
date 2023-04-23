# notes for BDP handshake demo

Still needs an example showing a realistic handshake process from Bluesky to
processing. For that demo:

- acquisition and processing need to agree (via handshake) "ready to start"
- acquisition signals start, emitting data (streams or files) to processing
- processing waits for "start processing" signal from acquisition (handshake)
- processing might signal interim status, results, or new instructions to acquisition
- acquisition signals "acquisition complete" (handshake)
- processing signals "processing complete", may include results
