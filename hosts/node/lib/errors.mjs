// One error type. The code is one of the DRIVER.md error codes.
export class ThouError extends Error {
  constructor(code, message, { notices = [], extra = {} } = {}) {
    super(message);
    this.code = code;
    this.notices = notices;
    this.extra = extra;
  }
}

export const badRequest = (message) => new ThouError('bad_request', message);
