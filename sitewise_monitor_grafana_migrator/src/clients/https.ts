import { request, RequestOptions } from 'https';

/**
 * httpsRequest calls the https library to make HTTPS requests
 * Used to interact with the Grafana HTTP APIs
 * @param options https request options
 * @param body request body for POST requests
 * @returns Promise with the request results
 */
export const httpsRequest = (options: RequestOptions, body?: any): Promise<any> => {
  return new Promise((resolve, reject) => {
    const req = request(options, (res) => {
      let data = '';

      res.on('data', (chunk) => {
        data += chunk;
      });

      res.on('end', () => {
        try {
          if (!!data) {
            const parsedData = JSON.parse(data);
            resolve(parsedData);
          } else {
            resolve(data);
          }
        } catch (e) {
          reject(e);
        }
      });
    });

    req.on('error', (e) => {
      reject(e);
    });

    if (body) {
      req.write(JSON.stringify(body));
    }

    req.end();
  });
};

// Only need GET and POST for Grafana HTTP APIs in this script
export const HTTPMethod = {
  GET: 'GET',
  POST: 'POST',
};