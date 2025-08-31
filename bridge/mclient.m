function [] = fsend(datapoints)

    startTime = tic;

    display(['more than ', num2str(datapoints), ' datapoints']);

    % server configuration
    %GUEST_IP = '192.168.56.102';
    GUEST_IP = '127.0.0.1';
    PORT = 8080;
    TIMEOUT = 30;
    
    % example data
    X1 = linspace(1, 1, datapoints);
    X2 = linspace(2,2, datapoints);
    data = struct( ...
        "X1", X1, ...
        "X2", X2 ...
        );
    display('data created');

    % serialization
    %payload = jsonencode(data);
    serData = msgpack('pack', data);
    display('data serialized');

    % send data to the server
    client = tcpclient(GUEST_IP, PORT, 'Timeout', TIMEOUT);
    % size
    dataLen = uint32(whos('serData').bytes);
    display(['sending ', num2str(dataLen), ' bytes']);
    write(client, swapbytes(dataLen), 'uint32');
    % data
    write(client, serData);
    display('data sent');

    % get the response from the server
    respLen = swapbytes(read(client, 1, 'uint32'));
    display(['receiving ', num2str(respLen), ' bytes']);

    % Read exact number of bytes for response
    response = read(client, respLen);

    % Decode response
    display('response received'); 
    result = msgpack('unpack', response);
    display('response deserialized');


    % clear the client
    clear client;

    elapsedTime = toc(startTime);
    display([num2str(elapsedTime), ' seconds elapsed']);
end