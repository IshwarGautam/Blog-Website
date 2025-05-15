const { Client } = require('pg');

exports.handler = async function(event, context) {
  const post_id = event.queryStringParameters?.post_id;

  if (!post_id) {
    return {
      statusCode: 400,
      body: JSON.stringify({ error: 'Missing post_id' }),
    };
  }

  const client = new Client({
    connectionString: process.env.DATABASE_URL,
    ssl: {
      rejectUnauthorized: false,
    },
  });

  try {
    await client.connect();

    const res = await client.query(
      `
      SELECT id, name, content, timestamp, parent_id
      FROM comments
      WHERE post_id = $1
      ORDER BY timestamp
    `,
      [post_id]
    );

    const comments = res.rows.map((row) => ({
      id: row.id,
      name: row.name,
      content: row.content,
      timestamp: row.timestamp.toISOString(),
      parent_id: row.parent_id,
    }));

    await client.end();

    return {
      statusCode: 200,
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(comments),
    };
  } catch (err) {
    console.error('DB error:', err);
    return {
      statusCode: 500,
      body: JSON.stringify({ error: 'Internal server error' }),
    };
  }
};
