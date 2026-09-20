# AWS setup for Phase 2

Everything here is run by **you**, in your own shell, against your own account.
I do not hold credentials, create accounts, or change billing settings.

## Why Phase 2 is on AWS at all, stated honestly

The laptop could do it. 502,579 records encode locally in about two hours and
faiss would handle the neighbour search. The two real reasons are:

1. **Disk.** One docket cost 886 MB and `ED-2021-OCR-0166` has 68x the record
   count of the docket already run, against 20 GB free at 90% full.
2. **The gap this project exists to close.** `gap_scan` measures AWS as a
   declared requirement in **215 of 586** target postings, 37%, triple the next
   item on the list. A project that closes that gap has to actually run there.

Reason 2 is a career reason, not a technical one, and it should be said out
loud rather than dressed up as necessity. It is still a good reason: the source
data already lives in S3, so reading it where it sits is the natural design
rather than a bolted-on one.

## Which kind of AWS account -- checked 2026-09-20, and one option breaks the build

**Do NOT use an AWS Educate Starter Account.** It is a sandbox: no Amazon
Bedrock, and no IAM role creation. `infra/main.tf` creates an IAM role, and the
whole Titan comparison arm is Bedrock, so both halves of Phase 2 fail. The $100
AWS Educate credit is real and is unusable for this project.

**Use a regular account on the current Free Tier.** Since 2025-07-15 a new
account gets **$100 in credits at signup, rising to $200 by using services --
and Bedrock is one of the named credit-earning services.** That covers the whole
sub-$50 Phase 2 estimate several times over.

At signup the account picks a plan, and the choice matters:

| | Free plan | Paid plan |
|---|---|---|
| spending past the credits | **structurally impossible** | bills at standard rates |
| account lifetime | closes at 6 months, or when credits run out | continues |

**Take the Free plan.** A budget under $50 against $100-200 of credits does not
need headroom, and making overspend impossible beats a billing alarm somebody
has to notice. The six-month expiry costs nothing here: `terraform destroy`
removes everything, and the corpus rebuilds from the public mirror on demand.

**Risk to check before the full batch run:** new AWS accounts carry very low
Bedrock throughput limits. On ~500k documents that means either a slow job or a
quota-increase request, and it is much better found in the console beforehand
than halfway through.

Accounts created **before 2025-07-15** are on the legacy 12-month free tier and
none of the above applies.

The GitHub Student Developer Pack is worth claiming with a `.edu` address, but
its cloud credits are Azure, DigitalOcean and Heroku rather than general AWS.
Worth one email to Khoury IT as well: some universities hold their own AWS
agreements that beat all of this. Unverified for Northeastern.

## One-time setup

```bash
brew install awscli
aws configure                 # or `aws configure sso` if your org uses SSO
aws sts get-caller-identity   # should print your account id
```

Sign up first at aws.amazon.com with the `.edu` address and pick the **Free
plan**. A card is required for identity verification; the Free plan does not
charge it.

```bash
cd ~/dev/comment-counts/infra
terraform init
terraform apply -var bucket_name=comment-counts-<something-unique-to-you>
```

Then export what it prints:

```bash
export COMMENT_COUNTS_BUCKET=...
export BEDROCK_BATCH_ROLE_ARN=...
```

**One step Terraform cannot do.** Bedrock model access is granted per account
by hand: **Bedrock console > Model access > Amazon Titan Text Embeddings V2 >
Enable**. Until that is done every batch job fails with `AccessDenied`, and the
error does not say model access is the reason.

## What gets created

| resource | why |
|---|---|
| one S3 bucket, encrypted, public access blocked | the corpus and the embeddings |
| lifecycle rule expiring `scratch/` after 30 days | intermediates are regenerable; this is what stops the bill growing after the analysis is done |
| lifecycle rule aborting incomplete multipart uploads | a failed 5 GB upload otherwise bills forever, invisibly |
| one IAM role for Bedrock batch | scoped to this bucket, with SourceAccount and SourceArn conditions against the confused-deputy problem |

No servers. The expensive things in this project are **jobs**, and a forgotten
server is the usual way a portfolio project becomes a bill. `terraform destroy`
removes everything, and `force_destroy = true` means it works even with objects
in the bucket, which is correct here because the corpus is rebuildable from a
public mirror at any time.

## Cost

Estimates to verify against current pricing, not quotes:

| item | rough |
|---|---|
| Titan embeddings, batch, ~500k documents | $10 – 20 |
| S3 storage, ~10 GB, one month | under $1 |
| requests and transfer | cents |
| **total for Phase 2** | **under $50** |

Reading `s3://mirrulations` is free and needs no credentials: it is a public
bucket, and this project never copies it wholesale. Only assembled text and
embeddings land in your bucket.

Set a billing alarm before the first batch job. The two line items that can
surprise, per the spec's own cost note, are OCR over scanned attachments and a
managed vector index. **Neither is in the Phase 2 plan** — attachment text is
already extracted in the mirror's `derived-data`, and exact blocked cosine is
fast enough at this scale that an ANN index would add a recall parameter to
defend for no speed that matters.

## The experiment this buys, beyond just running bigger

Phase 1 found that at matched precision, embeddings beat MinHash by **0.75
percentage points**. The fair objection is that this used a 22M-parameter model
with a 256-token window on documents whose median length is 1,361 characters.
Titan V2 has an 8,192-token window.

- If Titan also lands near 9%, the negative result stops being about the model.
- If it jumps, Phase 1's conclusion was about model capacity and gets restated.

**The threshold must be re-selected per model.** Cosine 0.97 on MiniLM is not
cosine 0.97 on Titan; comparing at a shared number compares calibration, not
ability. `bedrock_embed.select_threshold` picks each model's threshold on the
same labelled pairs at matched precision, and only then are collapses compared.

## Order of work

1. **You label the 25 pairs** (`.venv/bin/python label_pairs.py`, ~20 min).
   Everything downstream is threshold selection, and threshold selection is
   currently resting on labels a model wrote about its own output.
2. `src/agreement.py` for judge-human kappa. If kappa lands under 0.6, the
   spec's kill condition 4 applies and the machine labels get dropped.
3. Terraform apply, then Phase 2 corpus assembly to S3.
4. Titan batch embeddings, thresholds re-selected, cross-docket spread.

## Secrets

No key, token or credential belongs in this repo or in a chat message. The two
this project uses are both read from the environment and never written down:

```bash
export REGULATIONS_GOV_API_KEY=...     # free, api.data.gov, public data only
aws configure                          # writes ~/.aws/credentials, outside the repo
```

A key that has been pasted into a transcript should be regenerated rather than
reused, however low the consequence looks. Both of these are cheap to rotate.
