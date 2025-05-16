const { Client } = require("pg");

exports.handler = async function (event, context) {
  if (event.httpMethod !== "POST") {
    return {
      statusCode: 405,
      body: JSON.stringify({ error: "Method not allowed" }),
    };
  }

  let data;
  try {
    data = JSON.parse(event.body);
  } catch {
    return {
      statusCode: 400,
      body: JSON.stringify({ error: "Invalid JSON" }),
    };
  }

  const { slug, name, content, parent_id } = data;

  if (!slug || !name || !content) {
    return {
      statusCode: 400,
      body: JSON.stringify({ error: "Missing required fields" }),
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

    // Get post ID from slug
    const postRes = await client.query(
      `SELECT id FROM posts WHERE slug = $1`,
      [slug]
    );

    if (postRes.rowCount === 0) {
      return {
        statusCode: 404,
        body: JSON.stringify({ error: "Post not found" }),
      };
    }

    const post_id = postRes.rows[0].id;

    // Insert comment
    await client.query(
      `
      INSERT INTO comments (post_id, name, content, timestamp, parent_id)
      VALUES ($1, $2, $3, NOW(), $4)
    `,
      [post_id, name, content, parent_id || null]
    );

    await client.end();

    return {
      statusCode: 200,
      body: JSON.stringify({ message: "Comment posted successfully" }),
    };
  } catch (err) {
    console.error("DB error:", err);
    return {
      statusCode: 500,
      body: JSON.stringify({ error: "Internal server error" }),
    };
  }
};
