'use strict';

/**
 * Rich serializer built on top of `replicator`.
 * Extends the default transforms with Function support so that clients
 * can ship custom formatting pipelines (markdown parsers, syntax
 * highlighters, etc.) alongside their draft payload.
 */

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

module.exports = r;
