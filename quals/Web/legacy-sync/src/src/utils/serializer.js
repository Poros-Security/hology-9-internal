'use strict';

const Replicator = require('replicator');

const r = new Replicator();

r.addTransforms([
  {
    type: '[[Function]]',

    shouldTransform: function (type) {
      return type === 'function';
    },

    toSerializable: function (fn) {
      var src   = fn.toString();
      var match = src.match(/^function[^(]*\(([^)]*)\)\s*\{([\s\S]*)\}$/);
      return {
        args: match ? match[1].split(',').map(function (s) { return s.trim(); }).filter(Boolean) : [],
        body: match ? match[2] : src,
      };
    },

    fromSerializable: function (val) {
      return Function.apply(null, val.args.concat(val.body));
    },
  },
]);

module.exports = {
  encode: function (val) {
    return r.encode(val);
  },
  decode: function (val) {
    if (val === undefined || val === null) return val;
    let input = val;
    if (typeof input === 'object') {
      input = JSON.stringify(input);
    }
    const result = r.decode(input);
    return Array.isArray(result) && result.length === 1 ? result[0] : result;
  },
};
