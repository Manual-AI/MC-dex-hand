// Install the message handler before any asynchronous module initialization.
const ready = Promise.all([
  import("./environment.js").then(({ loadBowl }) => loadBowl()),
  import("./policy.js"),
  import("./lookahead.js"),
]);
let policy, model;
self.onmessage = async ({ data }) => {
  try {
    const [f, { BowlPolicy }, { choose }] = await ready;
    if (!policy) policy = new BowlPolicy(data.weights);
    if (model?.item.id !== data.object) {
      model?.dispose();
      model = f.create(f.catalog.find((item) => item.id === data.object));
    }
    const result = choose(model, policy, data.state, data.history, data.budget);
    postMessage({ request: data.request, ...result });
  } catch (e) {
    postMessage({ request: data.request, error: String(e.message || e) });
  }
};
