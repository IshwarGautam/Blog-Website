exports.handler = async function(event, context) {
  return {
    statusCode: 200,
    headers: {
      'Access-Control-Allow-Origin': '*',
      'Access-Control-Allow-Headers': 'Content-Type',
    },
    body: JSON.stringify({
      service_id: process.env.SERVICE_ID || "",
      template_id: process.env.TEMPLATE_ID || "",
      public_key: process.env.PUBLIC_KEY || ""
    })
  };
};
