const { Client } = require('pg');

exports.handler = async function(event, context) {
  const slug = event.queryStringParameters?.slug;

  if (!slug) {
    return {
      statusCode: 400,
      body: JSON.stringify({ error: 'Missing slug' }),
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
      SELECT c.id, c.name, c.content, c.timestamp, c.parent_id
      FROM comments c
      JOIN posts p ON c.post_id = p.id
      WHERE p.slug = $1
      ORDER BY c.timestamp
      `,
      [slug]
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
