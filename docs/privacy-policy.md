# Dincer Logistics Claude Connector Privacy Policy

**Effective date:** July 30, 2026

This connector-specific notice supplements the official
[Dincer Logistics Privacy and Cookie Policy](https://dincerlogistics.com/gizlilik-ve-cerez-politikasi/).
The official company policy is the primary privacy policy for the Anthropic
Directory listing.

Dincer Logistics operates the Dincer Logistics connector for Claude. This
policy explains how information is handled when you register for and use the
connector.

## Information we process

- Your email address, account status, and authentication records are processed
  by Amazon Cognito. Dincer Logistics does not receive your plaintext password.
- Questions sent through the connector and the matching workbook content are
  processed to return the requested answer.
- Technical records such as request time, status, error details, and service
  diagnostics may be stored in Amazon CloudWatch Logs.

## How we use information

Information is used only to authenticate users, provide the connector,
protect the service, troubleshoot failures, and meet legal or security
obligations. We do not sell personal information or use connector data for
advertising.

## Service providers and data flow

The connector uses Amazon Web Services, including Cognito, API Gateway,
Lambda, S3, and CloudWatch. Claude sends tool requests to the connector and
receives tool results, so Anthropic also processes that information under its
own terms and privacy policy. Source workbooks remain in Dincer Logistics'
AWS environment and are not stored in the public plugin repository.

## Retention and security

CloudWatch technical logs are retained for 30 days. Connector queries and
workbook results are processed transiently by Lambda; a short-lived in-memory
cache may exist only while a Lambda execution environment remains active.
Cognito account data is retained while the account is active or as required
for security and legal obligations.

Access to source data is read-only and limited to the approved AWS resources.
Traffic uses HTTPS, and users authenticate through OAuth 2.0 with Amazon
Cognito.

## Your choices

You may disconnect the connector in Claude at any time. To request access,
correction, or deletion of your connector account information, contact
[info@dincerlojistik.com](mailto:info@dincerlojistik.com).

## Changes

We may update this policy as the connector or legal requirements change. The
effective date above will be updated when changes are published.

## Contact

Dincer Logistics
[https://dincerlogistics.com/](https://dincerlogistics.com/)
[info@dincerlojistik.com](mailto:info@dincerlojistik.com)
