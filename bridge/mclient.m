function [] = fsend(datapoints)

    t1 = cputime;

    % server configuration
    %GUEST_IP = '192.168.56.102';
    GUEST_IP = '127.0.0.1';
    PORT = 8080;
    
    % example data
    distance = linspace(1, 1, datapoints);
    speed = linspace(2,2, datapoints);
    data = struct( ...
        "distance",distance, ...
        "speed", speed ...
        );

    % serialization (bottleneck)
    %payload = jsonencode(data);
    payload = msgpack('pack', data);
    display("data serialized, size in MB:");
    display([ ...
        'serialized data size ', ...
        num2str(whos('payload').bytes / (1024 * 1024)), ...
        'MB']);

    % send data to the server
    client = tcpclient(GUEST_IP, PORT);
    write(client, payload);

    % wait for the response
    % while client.NumBytesAvailable == 0
    %     pause(0.1);
    % end
    % response = read(client, 1, "uint8");
    % display(response);

    % clear the client
    clear client;

    t2 = cputime;
    display(['Elapsed time ', num2str(t2 - t1), ' seconds']);
end