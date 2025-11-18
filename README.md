# Future Vacations – Hiking Conditions Maps

Interactive Plotly maps that highlight month-by-month hiking conditions for every US national park. The project converts `data/national_parks_hiking_conditions.csv` into static HTML dashboards that you can open locally or host via GitHub Pages.

## Prerequisites

- Python 3.10+
- `pip` for dependency installation

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Generate maps locally

| Command | Result |
| --- | --- |
| `python main.py --month Apr` | Creates `output_maps/hiking_conditions_Apr.html` |
| `python main.py --all` | Rebuilds all month-specific HTML files in `output_maps/` |
| `python main.py --interactive` | Produces `output_maps/hiking_conditions_interactive.html` with a dropdown for Jan–Dec plus an Average tab |

The script also prints the park with the highest average score each time it runs.

## Deploy to GitHub Pages

This repo includes `.github/workflows/deploy-pages.yml`, a GitHub Actions workflow that builds the interactive dashboard and publishes it to GitHub Pages automatically.

1. Push this repository to GitHub.
2. In **Settings → Pages**, set **Build and deployment** to **GitHub Actions**.
3. The "Deploy hiking maps to GitHub Pages" workflow runs on every push to `main` (or manually via **Actions → Run workflow**). It:
   - Installs Python dependencies.
   - Runs `python main.py --interactive --outdir docs`.
   - Renames the generated HTML to `docs/index.html`.
   - Uploads `docs/` as the Pages artifact and deploys it.
4. Once the workflow succeeds, the published dashboard is available at `https://<your-user>.github.io/<repo-name>/`.

### Customizing the deployment

- To include additional static assets (images, CSS), place them in `docs/` after generation and before the upload step.
- If you rename the default branch or want to trigger deployments from feature branches, adjust the `on.push.branches` array in `.github/workflows/deploy-pages.yml`.
- For scheduled refreshes, add a `schedule` trigger to the workflow and commit updated data or automation scripts as needed.

## Project structure

```
main.py                    # Map generation logic
requirements.txt           # Python dependencies
.data/                     # Hiking condition CSV
output_maps/               # Local build artifacts
.github/workflows/         # CI/CD pipelines (GitHub Pages deploy)
docs/                      # GitHub Pages publication folder (generated)
```

Feel free to extend the dataset or styling—Plotly makes it straightforward to change color scales, projections, or hovertext formatting.
