import minimist from 'minimist';
import { createInterface } from 'readline';
import { promisify } from 'util';

/**
 * The command line arguments determine which steps of the process this script will run
 * 1. Create an Amazon Managed Grafana workspace
 * 2. Assign identities to workspace
 * 3. Create Grafana resources
 */

export interface Arguments {
  // Required for all steps
  portalId: string; // SWM portal to migrate to Amazon Managed Grafana
  region: string; // Region name (e.g. us-east-1)
  
  // Include to start at step 2
  workspaceId?: string; // Amazon Managed Grafana workspace created for the portal

  // Required for step 2
  // Omit to start at step 3
  instanceId?: string; // IAM Identity Center instance for identity application assignements
}

export const help = () => {
  console.log(`Configure the AWS credentials in your environment for the AWS CLI: https://docs.aws.amazon.com/cli/v1/userguide/cli-chap-configure.html
  
  Usage: 
  
    This script runs up to 3 steps to migrate your SiteWise Monitor resources into Amazon Managed Grafana resources:
    1. Create an Amazon Managed Grafana workspace
    2. Assign identities to workspace
    3. Create Grafana resources

    arguments:
      --region        REQUIRED
      --portalId      REQUIRED
      --workspaceId   OPTIONAL start at Step 2
      --instanceId    OPTIONAL required for Step 2, omit to start at Step 3

    You must provide a region and an IoT SiteWise portalId to migrate to Grafana. Then use an argument to decide what step to start at for your use case.
    For example, if you already created an Amazon Managed Grafana workspace, provide the --workspaceId argument. You need the --instanceId argument
    with the IAM Identity Center instance to assign identities to the Grafana workspace. Omit it if identities have already been assigned.
    
    Example migration of all portal resources to Grafana:
      npx ts-node src/index.ts --region us-east-1 --portalId 12345678-9012-3456-7890-abcdef123456 --instanceId ssoins-1234567890abcdef

    Example migration of portal resources to Amazon Managed Grafana workspace:
      npx ts-node src/index.ts --region us-east-1 --portalId 12345678-9012-3456-7890-abcdef123456 --workspaceId g-1234567890 --instanceId ssoins-1234567890abcdef
  
    Example migration of portal resources to a workspace with identities already assigned:
      npx ts-node src/index.ts --region us-east-1 --portalId 12345678-9012-3456-7890-abcdef123456 --workspaceId g-1234567890
    `);
};

// Parses command-line arguments for the sample files to extract the supported settings.
export const parseArgs = (): Arguments => {
  const args: Arguments = {
    portalId: '',
    region: '',
    workspaceId: '',
    instanceId: '',
  };
  const parsedArgs = minimist(process.argv.slice(2));
  for (const arg of Object.keys(parsedArgs)) {
    switch (arg) {
      case 'h':
      case 'help':
        help();
        process.exit(0);
      case 'portalId':
        args.portalId = parsedArgs[arg];
        break;
      case 'region':
        args.region = parsedArgs[arg];
        break;
      case 'workspaceId':
        args.workspaceId = parsedArgs[arg];
        break;
      case 'instanceId':
        args.instanceId = parsedArgs[arg];
        break;
      case '_':
        break;
      default:
        console.error(`unknown arg "--${arg}"`);
        help();
        process.exit(1);
    }
  }

  if (args.portalId === '' || args.region === '') {
    help();
    process.exit(1);
  }
  return args;
};

// TODO: get disclaimer verbage from security team
export const disclaimer = async () => {
    const dividingLine = '-------------------------------------------------';
    const disclaimerText = `${dividingLine}
... Something about accepting risk for creating IAM Roles and trust permissions ...
Would you like to opt-in? [yes/no]: `;

    const readLine = createInterface({
        input: process.stdin,
        output: process.stdout,
    });

    const question = promisify(readLine.question).bind(readLine);

    let answered = false;
    while (!answered) {
        const answer = await question(disclaimerText) as unknown as string;
        switch(answer.toLowerCase()) {
            case 'yes':
                answered = true;
                readLine.close();
                break;
            case 'no':
                console.log('Exiting...');
                process.exit(1);
            default:
                break;
        }
    }
    console.log(dividingLine);
}
