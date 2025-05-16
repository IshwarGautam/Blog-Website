const { Pool } = require("pg");

const pool = new Pool({
  connectionString: process.env.DATABASE_URL,
  ssl: { rejectUnauthorized: false }
});

exports.handler = async function (event) {
  const slug = event.queryStringParameters?.slug;

  if (!slug) {
    return {
      statusCode: 400,
      body: "Missing slug",
    };
  }

  try {
    // First get post_id from slug
    const postRes = await pool.query("SELECT id FROM posts WHERE slug = $1", [slug]);

    if (postRes.rows.length === 0) {
      return {
        statusCode: 404,
        body: "Post not found"
      };
    }

    const postId = postRes.rows[0].id;

    // Then get comments by post_id
    const commentRes = await pool.query(
      "SELECT * FROM comment WHERE post_id = $1 ORDER BY timestamp ASC",
      [postId]
    );

    return {
      statusCode: 200,
      body: JSON.stringify(commentRes.rows),
    };
  } catch (error) {
    console.error("Error fetching comments:", error);
    return {
      statusCode: 500,
      body: "Internal Server Error",
    };
  }
};
